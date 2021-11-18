import json
from copy import deepcopy
from os import listdir
from os.path import dirname, exists, isfile, join
from typing import List

from ruamel.yaml import YAML

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util

registry_path = join(dirname(dirname(__file__)), "config", "registry")
schemas_path = join(dirname(dirname(__file__)), "config", "registry", "schemas")
module_schemas_path = join(schemas_path, "modules")
opta_config_schemas_path = join(schemas_path, "opta-config-files")

CLOUD_FOLDER_NAMES = ["aws", "google", "azurerm"]

FOLDER_NAME_TO_CLOUD_LIST = {
    "aws": ["aws"],
    "azurerm": ["azure"],
    "google": ["gcp"],
    "common": ["aws", "azure", "gcp"],
}

CLOUD_NAME_TO_JSON_SCHEMA_NAME = {"aws": "aws", "google": "gcp", "azurerm": "azure"}


def _deep_equals(obj1: dict, obj2: dict) -> bool:
    """
    Deep compare two objects.
    """
    return json.dumps(obj1, sort_keys=True) == json.dumps(obj2, sort_keys=True)


def _get_json_schema_module_path(module_name: str) -> str:
    return join(module_schemas_path, f"{module_name}.json")


def _get_all_modules_names(cloud: str) -> list:
    dir_path = join(registry_path, cloud, "modules")
    return [
        f.split(".")[0]
        for f in listdir(dir_path)
        if isfile(join(dir_path, f)) and f.endswith("yaml")
    ]


def _get_module_json(module_name: str) -> dict:
    json_schema_file_path = _get_json_schema_module_path(module_name)

    if not exists(json_schema_file_path):
        raise Exception(
            f"No JSON Schema file detected for module {module_name}. Please create a file named {module_name}.json in the config/registry/schemas/modules"
        )

    json_schema_file = open(json_schema_file_path)
    module_json = json.load(json_schema_file)
    module_json["name"] = module_name
    return module_json


def _get_all_modules(cloud: str) -> List[dict]:
    module_names = _get_all_modules_names(cloud) + _get_all_modules_names("common")
    return [_get_module_json(module_name) for module_name in module_names]


def _check_opta_config_schemas(write: bool = False) -> None:
    for cloud in ["aws", "azurerm", "google"]:
        all_modules = _get_all_modules(cloud)
        json_schema_file_path = join(
            opta_config_schemas_path, f"env-{CLOUD_NAME_TO_JSON_SCHEMA_NAME[cloud]}.json"
        )

        json_schema_file = open(json_schema_file_path)
        json_schema = json.load(json_schema_file)
        new_json_schema = deepcopy(json_schema)

        allowed_module_ids = sorted(
            [
                module["$id"]
                for module in all_modules
                if module["opta_metadata"]["module_type"] == "environment"
            ]
        )
        new_json_schema["properties"]["modules"] = {
            "type": "array",
            "description": "The Opta modules to run in this environment",
            "items": {"oneOf": [module_id for module_id in allowed_module_ids]},
        }

        if write:
            with open(json_schema_file_path, "w") as f:
                json.dump(new_json_schema, f, indent=2)
        else:
            if not _deep_equals(new_json_schema, json_schema):
                print("------------EXPECTED SCHEMA-------------")
                print(json.dumps(new_json_schema, indent=2))
                print("------------ACTUAL SCHEMA-------------")
                print(json.dumps(json_schema, indent=2))
                raise Exception(
                    f"{json_schema_file_path} seems to be out of date. Rerun this script with the --write flag to fix this."
                )


def _check_module_schemas(write: bool = False) -> None:
    for cloud in ["aws", "azurerm", "google", "common"]:
        module_names = _get_all_modules_names(cloud)

        for module_name in module_names:
            module_registry_dict = yaml.load(
                open(join(registry_path, cloud, "modules", f"{module_name}.yaml"))
            )
            json_schema = _get_module_json(module_name)

            new_json_schema = deepcopy(json_schema)

            REQUIRED_FIELDS = ["description", "properties"]
            if any(p not in json_schema for p in REQUIRED_FIELDS):
                missing_fields = [
                    field for field in REQUIRED_FIELDS if field not in json_schema
                ]
                raise Exception(
                    f"JSON schema at for module {module_name} missing {missing_fields} field(s)"
                )

            new_json_schema["properties"]["type"] = {
                "description": "The name of this module",
                "enum": [module_name],
            }

            module_inputs = module_registry_dict["inputs"]
            for i in module_registry_dict["inputs"]:
                if i["user_facing"]:
                    input_name = i["name"]
                    if input_name not in json_schema["properties"]:
                        raise Exception(
                            f"property {input_name} is missing from json schema for module {module_name}"
                        )
                    new_input_property_dict = new_json_schema["properties"][input_name]

                    new_input_property_dict["description"] = i["description"]
                    if "default" in i:
                        new_input_property_dict["default"] = i["default"]

            new_json_schema["required"] = [
                i["name"]
                for i in module_inputs
                if i["user_facing"] and "required=True" in i["validator"]
            ] + ["type"]

            new_json_schema["opta_metadata"] = {
                "module_type": "environment"
                if module_registry_dict["environment_module"]
                else "service",
                "clouds": FOLDER_NAME_TO_CLOUD_LIST[cloud],
            }

            if write:
                json_schema_file_path = _get_json_schema_module_path(module_name)
                with open(json_schema_file_path, "w") as f:
                    json.dump(new_json_schema, f, indent=2)
            else:
                if not _deep_equals(new_json_schema, json_schema):
                    raise Exception(
                        f"Module {module_name}'s json schema file seems to be out of date. Rerun this script with the --write flag to fix this."
                    )


def check_schemas(write: bool = False) -> None:
    _check_module_schemas(write)
    _check_opta_config_schemas(write)
