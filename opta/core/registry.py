import os
from typing import Any, Dict, List

from ruamel.yaml import YAML

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util


def make_registry_dict() -> Dict[Any, Any]:
    registry_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "config", "registry"
    )
    registry_dict: Dict[Any, Any] = yaml.load(
        open(os.path.join(registry_path, "index.yaml"))
    )
    common_modules_path = os.path.join(registry_path, "common", "modules")
    with open(os.path.join(registry_path, "index.md"), "r") as f:
        registry_dict["text"] = f.read()
    for cloud in ["aws", "azurerm", "google"]:
        cloud_path = os.path.join(registry_path, cloud)
        cloud_dict = yaml.load(open(os.path.join(cloud_path, "index.yaml")))
        cloud_dict["modules"] = {}
        with open(os.path.join(cloud_path, "index.md"), "r") as f:
            cloud_dict["text"] = f.read()
        module_path = os.path.join(cloud_path, "modules")
        cloud_dict["modules"] = {
            **_make_module_registry_dict(module_path),
            **_make_module_registry_dict(common_modules_path),
        }
        registry_dict[cloud] = cloud_dict

    return registry_dict


def _make_module_docs(vanilla_text: str, module_dict: Dict[Any, Any]) -> str:
    input_lines: List[str] = []
    output_lines: List[str] = []
    input: Dict[str, Any]
    for input in module_dict["inputs"]:
        if not input["user_facing"]:
            continue
        required = "required=True" in input["validator"]
        name = input["name"]
        default = input["default"]
        description = input["description"]
        if required:
            input_lines.append(f"- {name} - Required. {description}")
        else:
            input_lines.append(f"- {name} - Optional. {description} Default {default}")

    output: Dict[str, Any]
    for output in module_dict["outputs"]:
        if not output["export"]:
            continue
        name = output["name"]
        description = output["description"]
        output_lines.append(f"- {name} - {description}")
    input_lines_block = "\n".join(input_lines)
    output_lines_block = "\n".join(output_lines)
    return f"{vanilla_text}\n\n## Fields\n\n##{input_lines_block}\n\n## Outputs\n\n{output_lines_block}"


def _make_module_registry_dict(directory: str) -> Dict[Any, Any]:
    if not os.path.exists(directory):
        raise Exception(f"Non-existing directory given as input: {directory}")
    module_names = [
        f.split(".")[0]
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.endswith("yaml")
    ]
    modules_dict = {}
    for module_name in module_names:
        module_dict = yaml.load(open(os.path.join(directory, f"{module_name}.yaml")))
        with open(os.path.join(directory, f"{module_name}.md"), "r") as f:
            module_dict["text"] = _make_module_docs(f.read(), module_dict)
        modules_dict[module_name] = module_dict
    return modules_dict


def make_registry_docs(directory: str) -> None:
    if not os.path.exists(directory):
        raise Exception(f"Non-existing directory given as input: {directory}")
    registry_dict = make_registry_dict()
    base_path = os.path.join(directory, "Reference")
    if os.path.exists(base_path):
        os.remove(base_path)
    os.makedirs(base_path)
    with open(os.path.join(base_path, "index.md")) as f:
        f.write(registry_dict["text"])
    for cloud in ["aws", "google", "azure"]:
        cloud_path = os.path.join(base_path, cloud)
        os.makedirs(cloud_path)
        cloud_dict = registry_dict[cloud]
        with open(os.path.join(cloud_path, "index.md")) as f:
            f.write(cloud_dict["text"])
        module_path = os.path.join(cloud_path, "modules")
        for module_name, module_dict in cloud_dict["modules"].items():
            with open(os.path.join(module_path, f"{module_name}.md")) as f:
                f.write(module_dict["text"])
