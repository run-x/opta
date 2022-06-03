import glob
import os
import shutil
from typing import Any, Dict, List

from ruamel.yaml import YAML

# Not using opta.utils.yaml since that would cause circular ref issues
yaml = YAML(typ="safe")

MODULE_INDEX = """---
title: "Modules"
linkTitle: "Modules"
weight: 1
description: This section provides the list of module types for the user to use in an Opta yaml for this cloud, along with their inputs and outputs.
---
"""


def make_registry_dict() -> Dict[Any, Any]:
    registry_path = _registry_path()
    with open(os.path.join(registry_path, "index.yaml")) as f:
        registry_dict: Dict[Any, Any] = yaml.load(f)
    with open(os.path.join(registry_path, "index.md"), "r") as f:
        registry_dict["text"] = f.read()
    module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")
    for cloud in ["aws", "azurerm", "google", "local", "helm"]:
        cloud_path = os.path.join(registry_path, cloud)
        with open(os.path.join(cloud_path, "index.yaml")) as f:
            cloud_dict = yaml.load(f)
        cloud_dict["modules"] = {}
        with open(os.path.join(cloud_path, "index.md"), "r") as f:
            cloud_dict["text"] = f.read()
        if cloud == "azurerm":
            alt_cloudname = "azure"
        elif cloud == "google":
            alt_cloudname = "gcp"
        elif cloud == "helm":
            # use the local modules since byok is cloud agnostic, we don't want to create resources like IAM and such
            alt_cloudname = "local"
        else:
            alt_cloudname = cloud
        cloud_dict["modules"] = {**_make_module_registry_dict(module_path, alt_cloudname)}
        registry_dict[cloud] = cloud_dict
    return registry_dict


INPUTS_TABLE_HEADING = """
| Name      | Description | Default | Required |
| ----------- | ----------- | ------- | -------- |
"""

OUTPUTS_TABLE_HEADING = """
| Name      | Description |
| ----------- | ----------- |
"""


def _make_module_docs(vanilla_text: str, module_dict: Dict[Any, Any]) -> str:
    input_lines: List[str] = []
    output_lines: List[str] = []
    inputs: Dict[str, Any]
    for inputs in module_dict["inputs"]:
        if not inputs["user_facing"]:
            continue
        name = inputs["name"]
        if "default" in inputs:
            default = f"`{inputs['default']}`"
        else:
            default = "*none*"

        description = inputs["description"].replace("\n", " ")
        required = "required=True" in inputs["validator"]
        table_row = f"| `{name}` | {description} | {default} | {required} |"
        input_lines.append(table_row)

    output: Dict[str, Any]
    for output in module_dict["outputs"]:
        if not output["export"]:
            continue
        name = output["name"]
        description = output["description"].replace("\n", " ")
        table_row = f"| `{name}` | {description} |"
        output_lines.append(table_row)

    result = f"{vanilla_text}\n\n"
    if len(input_lines) > 0:
        result += "## Fields\n\n"
        result += INPUTS_TABLE_HEADING + "\n".join(input_lines)
    if len(output_lines) > 0:
        result += "\n\n## Outputs\n\n"
        result += OUTPUTS_TABLE_HEADING + "\n".join(output_lines)
    return result


def _get_all_module_info(directory: str, cloud: str) -> list:
    """
    Return a list of tuples: (module_name, yaml_path, md_path)
    """
    rtn_list = []
    all_yaml_files = glob.glob(directory + "/**/*.yaml", recursive=True)
    all_md_files = glob.glob(directory + "/**/*.md", recursive=True)
    for a_yaml_path in all_yaml_files:
        try:
            with open(a_yaml_path) as f:
                module_dict = yaml.load(f)
            if not module_dict:
                continue
        except:  # nosec # noqa
            continue
        if "clouds" not in module_dict:
            continue
        if cloud not in module_dict["clouds"]:
            continue
        module_name = os.path.basename(a_yaml_path).split(".yaml")[0]

        # try loading cloud specific .md first
        module_md_files = [
            f for f in all_md_files if os.path.basename(f) == f"{cloud}-{module_name}.md"
        ]
        if not module_md_files:
            # expect a generic module .md
            module_md_files = [
                f for f in all_md_files if os.path.basename(f) == f"{module_name}.md"
            ]
        if not module_md_files:
            raise Exception(
                f"Can't find .md file for module {module_name}, cloud {cloud}"
            )
        a_md_path = module_md_files[0]

        rtn_list.append((module_name, a_yaml_path, a_md_path))
    return rtn_list


def _make_module_registry_dict(directory: str, cloud: str = "") -> Dict[Any, Any]:
    if not os.path.exists(directory):
        raise Exception(f"Non-existing directory given as input: {directory}")
    modules_dict = {}
    cloud_yamls_module_names = _get_all_module_info(directory, cloud)
    for module_name, a_yaml_path, a_md_path in cloud_yamls_module_names:
        try:
            with open(a_yaml_path) as f:
                module_dict = yaml.load(f)
            if not module_dict:
                continue
        except:  # nosec # noqa
            continue
        with open(a_md_path, "r") as f:
            module_dict["text"] = _make_module_docs(f.read(), module_dict)
        for input in module_dict["inputs"]:
            input["required"] = (
                input["user_facing"] and "required=True" in input["validator"]
            )
        module_dict["validators"] = _make_module_validators(module_dict)
        image_types = ("png", "jpg", "jpeg")
        module_image_files = []
        for image_type in image_types:
            module_image_files.extend(
                glob.glob(
                    os.path.dirname(a_md_path) + "/**/*." + image_type, recursive=True
                )
            )
        module_dict["image_files"] = module_image_files
        module_name = module_dict.get("name_override", module_name)
        modules_dict[module_name] = module_dict
    return modules_dict


def _make_module_validators(module_dict: Dict) -> List[Dict]:
    main_validator: Dict[Any, Any] = {
        "type": "str(required=True)",
        "name": "str(required=False)",
        "depends_on": "list(str(), required=False)",
    }
    for input in module_dict["inputs"]:
        if not input["user_facing"]:
            continue
        main_validator[input["name"]] = input["validator"]

    validator_list = [main_validator]
    if module_dict.get("extra_validators"):
        validator_list.append(module_dict["extra_validators"])
    return validator_list


def make_registry_docs(directory: str) -> None:
    if not os.path.exists(directory):
        raise Exception(f"Non-existing directory given as input: {directory}")
    registry_dict = make_registry_dict()
    registry_path = _registry_path()
    base_path = os.path.join(directory, "Reference")
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)
    image_path = os.path.join(directory, "static", "reference_images")
    if os.path.exists(image_path):
        shutil.rmtree(image_path)
    os.makedirs(image_path)
    with open(os.path.join(base_path, "_index.md"), "w") as f:
        f.write(registry_dict["text"])
    for cloud in ["aws", "google", "azurerm"]:
        cloud_path = os.path.join(base_path, cloud)
        os.makedirs(cloud_path)
        cloud_dict = registry_dict[cloud]

        # copy cloud documentation
        from_dir = os.path.join(registry_path, cloud)
        to_dir = os.path.join(cloud_path)
        shutil.copytree(from_dir, to_dir, dirs_exist_ok=True)
        shutil.move(
            os.path.join(cloud_path, "index.md"), os.path.join(cloud_path, "_index.md")
        )

        # copy module documentation
        module_path = os.path.join(cloud_path, "modules")
        os.makedirs(module_path)
        with open(os.path.join(module_path, "_index.md"), "w") as f:
            f.write(MODULE_INDEX)

        for module_name, module_dict in cloud_dict["modules"].items():
            with open(os.path.join(module_path, f"{module_name}.md"), "w") as f:
                f.write(module_dict["text"])
            image_destination = os.path.join(image_path, cloud, module_name)
            if not os.path.exists(image_destination):
                os.makedirs(image_destination)
            for image_file in module_dict["image_files"]:
                shutil.copy(image_file, image_destination)


def _registry_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "registry")
