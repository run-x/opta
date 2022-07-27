import datetime
import json
import os
import shutil
import tempfile  # nosec
from typing import Dict, List, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.local_flag import _clean_folder, _clean_tf_folder
from opta.constants import REGISTRY, TF_FILE_PATH, VERSION
from opta.core.generator import gen, gen_opta_resource_tags
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module
from opta.pre_check import pre_check
from opta.utils import check_opta_file_exists, dicts, logger
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    str_options,
)
from opta.utils.markdown import Code, Markdown, Text, Title1, Title2


@click.command()
@click.option(
    "-d", "--directory", help="Directory for output", show_default=False,
)
@click.option(
    "--readme-format",
    type=click.Choice(["none", "md", "html"], case_sensitive=False),
    default="html",
    help="Readme format",
    show_default=True,
)
@click.option(
    "--delete",
    is_flag=True,
    default=False,
    help="""Delete the existing directory if it already exists.
    Warning: If used, the existing files will be lost, including the terraform state files if local backend is used.""",
    show_default=True,
)
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    help="Automatically approve confirmation message for deleting existing files.",
)
@click.option(
    "--backend",
    type=click.Choice(["local", "remote"], case_sensitive=False),
    default="local",
    help="Terraform backend type. If you have no underlying infrastructure, 'local' would get you started. If you have already provisonned your infrastructure with opta use 'remote' to import the current state.",
    show_default=True,
)
@config_option
@env_option
@input_variable_option
@click.pass_context
def generate_terraform(
    ctx: click.Context,
    config: str,
    env: Optional[str],
    directory: Optional[str],
    readme_format: str,
    delete: bool,
    auto_approve: bool,
    backend: str,
    var: Dict[str, str],
) -> None:
    """(beta) Generate Terraform language files

    Examples:

    opta generate-terraform -c my-config.yaml

    opta generate-terraform -c my-config.yaml --directory ./terraform

    opta generate-terraform -c my-config.yaml --auto-approve --backend remote --readme-format md
    """

    print("This command is in beta mode")
    print(
        "If you have any error or suggestion, please let us know in our slack channel  https://slack.opta.dev\n"
    )

    config = check_opta_file_exists(config)

    pre_check()
    _clean_tf_folder()

    layer = Layer.load_from_yaml(config, env, stateless_mode=True, input_variables=var)
    layer.validate_required_path_dependencies()

    if directory is None:
        # generate the target directory
        directory = f"gen-tf-{layer.name}"
        if env is not None:
            directory = f"{directory}-{env}"

    if directory.strip() == "":
        # the users sets it to empty
        raise click.UsageError("--directory can't be empty")

    event_properties: Dict = layer.get_event_properties()
    event_properties["modules"] = ",".join([m.get_type() for m in layer.get_modules()])
    amplitude_client.send_event(
        amplitude_client.START_GEN_TERRAFORM_EVENT, event_properties=event_properties,
    )

    try:

        # work in a temp directory until command is over, to not leave a partially generated folder
        tmp_dir_obj = tempfile.TemporaryDirectory(prefix="opta-gen-tf")
        tmp_dir = tmp_dir_obj.name

        # quick exit if directory already exists and not empty
        output_dir = os.path.join(os.getcwd(), directory)
        if _dir_has_files(output_dir):
            if not delete:
                raise UserErrors(
                    f"Error: Output directory already exists: '{output_dir}'. If you want to delete it, use the '--delete' option"
                )
            print(
                f"Output directory {output_dir} already exists and --delete flag is on, deleting it"
            )
            if not auto_approve:
                state_file_warning = (
                    ", including terraform state files"
                    if os.path.exists(os.path.join(output_dir, "tfstate"))
                    else ""
                )
                click.confirm(
                    f"The output directory will be deleted{state_file_warning}: {output_dir}.\n Do you approve?",
                    abort=True,
                )
            _clean_folder(output_dir)

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
        # note this will only copy the 'tf_module' subdirectory ex: modules/aws_base/tf_module
        for module in layer.modules:
            src_path = module.module_dir_path
            if not os.path.exists(src_path):
                logger.warning(
                    f"Could not find source directory for module '{module.name}', ignoring it"
                )
                # dynamically mark it as not exportable
                module.desc["is_exportable"] = False
                continue
            rel_path = "./" + src_path[src_path.index("modules/") :]
            abs_path = os.path.join(tmp_dir, rel_path)
            logger.debug(f"Copying module from {module.get_type()} to {abs_path}")
            shutil.copytree(src_path, abs_path, dirs_exist_ok=True)
            # configure module path to use new relative path
            module.module_dir_path = rel_path
            # if there is some export documentation load it now - it will be added to the readme
            export_md = os.path.join(src_path, "..", "export.md")
            if os.path.exists(export_md):
                with open(export_md, "r") as f:
                    module.desc["export"] = f.read()

        # update terraform backend to be local (currently defined in the registry)
        # this is needed as the generated terraform should work outside of opta
        original_backend = REGISTRY[layer.cloud]["backend"]
        if backend.lower() == "local":
            backend_dir = f"./tfstate/{layer.root().name}.tfstate"
            logger.debug(f"Setting terraform backend to local: {backend_dir}")
            REGISTRY[layer.cloud]["backend"] = {"local": {"path": backend_dir}}
        # generate the main.tf.json
        try:
            execution_plan = list(gen(layer))
        finally:
            REGISTRY[layer.cloud]["backend"] = original_backend

        # break down json file in multiple files
        with open(TF_FILE_PATH) as f:
            main_tf_json = json.load(f)

        for key in ["provider", "data", "output", "terraform"]:
            # extract the relevant json
            main_tf_json, extracted_json = dicts.extract(main_tf_json, key)

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
        opta_cmd = f"opta {ctx.info_name} {str_options(ctx)}"
        readme_file = _generate_readme(
            layer, execution_plan, tmp_dir, readme_format, opta_cmd, backend
        )

        # we have a service file but the env was not exported
        if layer.name != layer.root().name and not os.path.exists(
            os.path.join(output_dir, "module-base.tf.json")
        ):
            print(
                f"Warning: the output directory doesn't include terraform files for the environment named '{layer.root().name}', "
                "some dependencies might be missing for terraform to work."
            )

        # if everything was successfull, copy tmp dir to target dir
        logger.debug(f"Copy {tmp_dir} to {output_dir}")
        shutil.copytree(tmp_dir, output_dir, dirs_exist_ok=True)
        unsupported_modules = [m for m in layer.get_modules() if not m.is_exportable()]

        if unsupported_modules:
            unsupported_modules_str = ",".join(
                [m.get_type() for m in unsupported_modules]
            )
            event_properties["unsupported_modules"] = unsupported_modules_str
            print(
                f"Terraform files partially generated, a few modules are not supported: {unsupported_modules_str}"
            )
        else:
            print("Terraform files generated successfully.")
        if readme_file:
            copied_readme = os.path.join(output_dir, os.path.basename(readme_file))
            print(f"Check {copied_readme} for documentation.")

    except Exception as e:
        event_properties["success"] = False
        event_properties["error_name"] = e.__class__.__name__
        raise e
    else:
        event_properties["success"] = True
    finally:
        amplitude_client.send_event(
            amplitude_client.FINISH_GEN_TERRAFORM_EVENT,
            event_properties=event_properties,
        )

        tmp_dir_obj.cleanup()


def _write_json(data: dict, file_path: str) -> None:
    logger.debug(f"Writing file: {file_path}")
    with open(file_path, "w") as f:
        f.write(json.dumps(data, indent=2))


def _generate_readme(
    layer: Layer,
    execution_plan: list,
    output_dir: str,
    format: str,
    opta_command: str,
    backend: str,
) -> Optional[str]:
    """generate the readme, returns the generated file if any.

    :param layer: current layer
    :param execution_plan return value for opta.core.generator.gen()
    :param output_dir directory for the readme
    :param format one of 'md', 'html', 'none'
    :param opta_command current opta command, included in the readme
    """

    if format.lower() == "none":
        return None

    readme = Markdown()
    readme >> Title1(f"Terraform stack {layer.name}")
    readme >> Text(
        "Follow the steps defined in this document to allow the depending resources to be created in the expected order."
    )
    readme >> Title2("Check the backend configuration")
    if backend.lower() == "local":
        readme >> Text(
            """The terraform file [terraform.tf.json](./terraform.tf.json) comes pre-configured
        to use a local terraform state file."""
        )
    else:
        readme >> Text(
            """The terraform file [terraform.tf.json](./terraform.tf.json) comes pre-configured
        to point to the remote backend used by opta."""
        )
        readme >> Text(
            """The first time `terraform plan` is executed, you will see a message `Note: Objects have changed outside of Terraform`.
            This is expected, running the subsequent `terraform apply` will import the remote state."""
        )

    readme >> Text(
        """If you want to use a different backend, change the section `terraform/backend`.
        See the [terraform documentation](https://www.terraform.io/language/settings/backends) for supported backends."""
    )
    readme >> Title2("Initialize Terraform")
    readme >> Code("terraform init")

    def add_custom_export(modules: List[Module]) -> None:
        for module in modules:
            export_doc = module.desc.get("export", "")
            if export_doc:
                readme >> Text(export_doc)

    covered_modules: list = []
    for module_idx, _, _ in execution_plan:

        new_modules, unsupported_modules = [], []
        for m in layer.get_modules(module_idx):
            if m in covered_modules:
                continue
            elif m.is_exportable():
                new_modules.append(m)
            elif m not in unsupported_modules:
                unsupported_modules.append(m)

        if unsupported_modules:
            readme >> Title2(
                f"Unsupported {_print_modules(unsupported_modules, prefix='module')}"
            )
            readme >> Text(
                f"Exporting {_print_modules(unsupported_modules, prefix='module')} is not supported at this time."
            )
            add_custom_export(unsupported_modules)

        # Add terraform instructions for current step
        if new_modules:
            readme >> Title2(
                f"Execute Terraform for {_print_modules(new_modules, prefix='module')}"
            )
            if not covered_modules:
                if layer.parent is None:
                    # first step for environment provisioning
                    readme >> Text("This step has no dependency.")
                else:
                    # first step for a service
                    readme >> Text(
                        f"This step depends on the terraform stack '{layer.parent.name}'."
                    )
            else:
                readme >> Text(
                    f"This step depends on {_print_modules(covered_modules, prefix='module')}."
                )
            readme >> Text(
                f"This step will execute terraform for the {_print_modules(new_modules, prefix='module')}."
            )
            readme >> Code(
                f"""terraform plan -compact-warnings -lock=false -input=false -out=tf.plan {_print_modules(list=new_modules, name_prefix='-target=module.', separator=' ')}"""
            )
            readme >> Code("terraform apply -compact-warnings -auto-approve tf.plan")
            add_custom_export(new_modules)

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
        f"""terraform plan -compact-warnings -lock=false -input=false -out=tf.plan {_print_modules(list=covered_modules, name_prefix='-target=module.', separator=' ')} -destroy"""
    )
    readme >> Code("terraform apply -compact-warnings -auto-approve tf.plan")

    readme >> Title2("Additional information")
    readme >> Text("This file was generated by [opta](https://github.com/run-x/opta).")
    readme >> Text(f"- opta version: {VERSION}")
    readme >> Text(f"- Command (including default values): `{opta_command}`")
    readme >> Text(f"- Generated at: {datetime.datetime.now()}")
    target_path = os.path.join(output_dir, f"readme-{layer.name}.{format}")
    logger.debug(f"Writing file: {target_path}")
    readme.write(target_path) if format.lower() == "md" else readme.writeHTML(target_path)
    return target_path


def _print_modules(
    list: List[Module], separator: str = ", ", prefix: str = "", name_prefix: str = ""
) -> str:
    list_str = separator.join([f"{name_prefix}{m.name}" for m in list])
    if prefix:
        # add trailing s if plural
        prefix = prefix if len(list) <= 1 else f"{prefix}s"
        return f"{prefix} {list_str}"
    return list_str


def _dir_has_files(path: str) -> bool:
    if os.path.exists(path):
        return len(os.listdir(path)) != 0
    # not exist
    return False
