import datetime
import json
import os
import shutil
import tempfile  # nosec
from typing import Dict, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.local_flag import _clean_folder, _clean_tf_folder
from opta.constants import REGISTRY, TF_FILE_PATH, VERSION
from opta.core.generator import gen, gen_opta_resource_tags
from opta.layer import Layer
from opta.pre_check import pre_check
from opta.utils import check_opta_file_exists, dicts, logger
from opta.utils.clickoptions import str_options
from opta.utils.markdown import Code, Markdown, Text, Title1, Title2


@click.command()
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
@click.option(
    "-e",
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "-d",
    "--directory",
    default="./generated-terraform",
    help="Directory for output",
    show_default=True,
)
@click.option(
    "--replace",
    is_flag=True,
    default=False,
    help="""Replace the existing directory if it already exists.
    Warning: If used, the existing files will be lost, including the terraform state files if local backend is used.""",
    show_default=True,
)
@click.pass_context
def generate_terraform(
    ctx: click.Context, config: str, env: Optional[str], directory: str, replace: bool
) -> None:
    """Generate Terraform language files

    Examples:

    opta generate-terraform -c my-config.yaml

    opta generate-terraform -c my-config.yaml -d ./tf
    """

    if directory.strip() == "":
        raise click.UsageError("--directory can't be empty")

    config = check_opta_file_exists(config)

    pre_check()
    _clean_tf_folder()

    layer = Layer.load_from_yaml(config, env, stateless_mode=True)

    layer.validate_required_path_dependencies()

    event_properties: Dict = layer.get_event_properties()
    amplitude_client.send_event(
        amplitude_client.GEN_TERRAFORM, event_properties=event_properties,
    )

    # work in a temp directory until command is over, to prevent messing up existing files
    tmp_dir = tempfile.TemporaryDirectory(prefix="opta-gen-tf").name
    output_dir = os.path.join(os.getcwd(), directory)

    # to keep consistent with what opta does - we could make this an option if opta tags are not desirable
    gen_opta_resource_tags(layer)

    # copy helm service dir
    if "k8s-service" in [m.type for m in layer.modules]:
        # find module root directory
        service_helm_dir = os.path.join(
            layer.modules[0].module_dir_path, "..", "..", "opta-k8s-service-helm"
        )
        target_dir = os.path.join(tmp_dir, "modules", "opta-k8s-service-helm")
        logger.debug(f"Copying helm charts from {service_helm_dir} to {target_dir}")
        shutil.copytree(service_helm_dir, target_dir, dirs_exist_ok=True)

    # copy module directories and update the module path to point to local directory
    for module in layer.modules:
        src_path = module.module_dir_path
        rel_path = "./" + src_path[src_path.index("modules/") :]
        abs_path = os.path.join(tmp_dir, rel_path)
        logger.debug(f"Copying module from {module.aliased_type} to {abs_path}")
        shutil.copytree(src_path, abs_path, dirs_exist_ok=True)
        # configure module path to use new relative path
        module.module_dir_path = rel_path

    # update terraform backend to be local (currently defined in the registry)
    # this is needed as the generated terraform should work outside of opta
    backend_dir = f"./tfstate/{layer.root().name}.tfstate"
    logger.debug(f"Setting terraform backend to local: {backend_dir}")
    original_backend = REGISTRY[layer.cloud]["backend"]
    REGISTRY[layer.cloud]["backend"] = {"local": {"path": backend_dir}}
    # generate the main.tf.json
    try:
        execution_plan = list(gen(layer))
    finally:
        REGISTRY[layer.cloud]["backend"] = original_backend

    # break down json file in multiple files
    main_tf_json = json.load(open(TF_FILE_PATH))
    for key in ["provider", "data", "output", "terraform"]:
        # extract the relevant json
        main_tf_json, extracted_json = dicts.extract(main_tf_json, key)

        # if there was already a file for it, merge it
        # ex: combine all the terraform "output" variables
        prev_tf_file = os.path.join(output_dir, f"{key}.tf.json")
        if os.path.exists(prev_tf_file):
            logger.debug(
                f"Found existing terraform file: {prev_tf_file}, merging it with new values"
            )
            prev_json = json.load(open(prev_tf_file))
            extracted_json = dicts.merge(extracted_json, prev_json)

        # save it as it's own file
        _write_json(extracted_json, os.path.join(tmp_dir, f"{key}.tf.json"))

    # extract modules tf.json in their own files
    main_tf_json, modules_json = dicts.extract(main_tf_json, "module")
    for name, value in modules_json["module"].items():
        _write_json(
            {"module": {name: value}}, os.path.join(tmp_dir, f"module-{name}.tf.json")
        )

    # update the main file without the extracted sections
    if main_tf_json:
        # only write file there is anything remaining
        _write_json(
            main_tf_json, os.path.join(tmp_dir, f"{tmp_dir}/{layer.name}.tf.json")
        )

    # generate the readme
    readme_name = f"{layer.name}.md"
    opta_cmd = f"opta {ctx.info_name} {str_options(ctx)}"
    _generate_readme(layer, execution_plan, f"{tmp_dir}/{readme_name}", opta_cmd)

    # if everything was successfull, copy tmp dir to target dir
    if os.path.exists(output_dir):
        if replace:
            logger.info(
                f"Output directory {directory} already exists and --replace flag is on, deleting it"
            )
            _clean_folder(output_dir)
        else:
            logger.info(
                f"Output directory {directory} already exists, adding new files to it"
            )

    logger.debug(f"Copy {tmp_dir} to {output_dir}")
    shutil.copytree(tmp_dir, output_dir, dirs_exist_ok=True)
    logger.info(
        f"Terraform files generated, check {os.path.join(directory, readme_name)} for documentation"
    )


def _write_json(data: dict, file_path: str) -> None:
    logger.debug(f"Writing file: {file_path}")
    with open(file_path, "w") as f:
        f.write(json.dumps(data, indent=2))


def _generate_readme(
    layer: Layer, execution_plan: list, target_path: str, opta_command: str
) -> None:
    readme = Markdown()
    readme >> Title1(f"Terraform stack {layer.name}")
    readme >> Text(
        "Follow the steps defined in this document to allow the depending resources to be created in the expected order."
    )
    readme >> Title2("Check the backend configuration")
    readme >> Text(
        """The terraform file [provider.tf.json](./provider.tf.json) comes pre-configured
    to point to a local terraform state file. If you want to use a remote state instead,
    change the section `terraform/backend`. See the terraform documentation for supported backends."""
    )
    readme >> Title2("Initialize Terraform")
    readme >> Code("terraform init")
    covered_modules: list = []
    for module_idx, _, _ in execution_plan:
        new_modules = [
            m.name for m in layer.get_modules(module_idx) if m.name not in covered_modules
        ]

        # Add terraform instructions for current step
        readme >> Title2(f"Execute Terraform for {_print_list('module', new_modules)}")
        if not covered_modules:
            if layer.parent is None:
                # first step for environment provisioning
                readme >> Text("This step has no dependency.")
            else:
                # first step for a service
                readme >> Text(f"This step depends on the stack '{layer.parent.name}'.")
        else:
            readme >> Text(
                f"This step depends on {_print_list('module', covered_modules)}."
            )
        readme >> Text(
            f"This step will execute terraform for the {_print_list('module', new_modules)}."
        )
        readme >> Code(
            f"""terraform plan -compact-warnings -lock=false -input=false -out=tf.plan {" ".join([f"-target=module.{name}" for name in new_modules])}"""
        )
        readme >> Code("terraform apply -compact-warnings -auto-approve tf.plan")

        # add modules as covered
        covered_modules = covered_modules + new_modules

    if layer.parent is None:
        readme >> Title2("Execute Terraform for the services")
        readme >> Text(
            "If you have terraform files for some services, you can executed them at this stage."
        )

    readme >> Title2("Destroy")
    readme >> Text("To destroy all remote objects, run:")
    readme >> Code(
        f"""terraform plan -compact-warnings -lock=false -input=false -out=tf.plan {" ".join([f"-target=module.{name}" for name in covered_modules])} -destroy"""
    )
    readme >> Code("terraform apply -compact-warnings -auto-approve tf.plan")

    readme >> Title2("Additional information")
    readme >> Text(
        f"""This file was generated by opta.
        - opta version: {VERSION}
        - Command: `{opta_command}`
        - Generated at: {datetime.datetime.now()}"""
    )

    logger.debug(f"Writing readme file: {target_path}")
    readme.write(target_path)


def _print_list(word: str, list: list, separator: str = ", ") -> str:
    list_str = separator.join(list)
    word = word if len(list) <= 1 else f"{word}s"
    return f"{word} {list_str}"
