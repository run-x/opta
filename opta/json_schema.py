import json
from copy import deepcopy
from os.path import dirname, exists, join
from typing import List

from opta.registry import _get_all_module_info
from opta.utils import yaml

registry_path = join(dirname(dirname(__file__)), "config", "registry")
schemas_path = join(dirname(dirname(__file__)), "config", "registry", "schemas")
modules_path = join(dirname(dirname(__file__)), "modules")

opta_config_schemas_path = join(schemas_path, "opta-config-files")

CLOUD_FOLDER_NAMES = ["aws", "google", "azurerm", "local"]

FOLDER_NAME_TO_CLOUD_LIST = {
    "aws": ["aws"],
    "azurerm": ["azure"],
    "google": ["gcp"],
    "common": ["aws", "azure", "gcp"],
    "local": ["local"],
}

CLOUD_NAME_TO_JSON_SCHEMA_NAME = {
    "aws": "aws",
    "google": "gcp",
    "azurerm": "azure",
    "local": "local",
}


CONFIG_TYPE_ENV = "env"
CONFIG_TYPE_SERVICE = "service"
CONFIG_TYPES = [CONFIG_TYPE_ENV, CONFIG_TYPE_SERVICE]


def _deep_equals(obj1: dict, obj2: dict) -> bool:
    """
    Deep compare two objects.
    """
    return json.dumps(obj1, sort_keys=True) == json.dumps(obj2, sort_keys=True)


def _get_json_schema_module_path(module_name: str, directory: str) -> str:
    return join(directory, f"{module_name}.json")


def _get_module_json(module_name: str, directory: str) -> dict:
    json_schema_file_path = _get_json_schema_module_path(module_name, directory)

    if not exists(json_schema_file_path):
        raise Exception(
            f"No JSON Schema file detected for module {module_name}. Please create a file named {module_name}.json in the modules' subdirectory for this module."
        )

    with open(json_schema_file_path) as json_schema_file:
        module_json = json.load(json_schema_file)

    module_json["name"] = module_name
    return module_json


def _get_all_modules(cloud: str) -> List[dict]:
    module_info = _get_all_module_info(modules_path, cloud)
    rtn_array = []
    for module_name, yaml_path, _ in module_info:
        rtn_array.append(_get_module_json(module_name, dirname(yaml_path)))
    return rtn_array


def _check_opta_config_schemas(write: bool = False) -> None:
    for cloud in CLOUD_FOLDER_NAMES:
        for config_type in CONFIG_TYPES:
            cloudjs = CLOUD_NAME_TO_JSON_SCHEMA_NAME[cloud]
            all_modules = _get_all_modules(cloudjs)
            json_schema_file_path = join(
                opta_config_schemas_path, f"{cloudjs}-{config_type}.json",
            )

            with open(json_schema_file_path) as json_schema_file:
                json_schema = json.load(json_schema_file)
            new_json_schema = deepcopy(json_schema)

            allowed_module_ids = sorted(
                [
                    module["$id"]
                    for module in all_modules
                    if module["opta_metadata"]["module_type"] == config_type
                ]
            )
            new_json_schema["properties"]["modules"] = {
                "type": "array",
                "description": "The Opta modules to run in this environment",
                "items": {
                    "oneOf": [{"$ref": module_id} for module_id in allowed_module_ids]
                },
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
    for cloud in ["aws", "azurerm", "google", "local"]:
        with open(join(registry_path, cloud, "index.yaml")) as f:
            index_yaml = yaml.load(f)

        module_info = _get_all_module_info(
            modules_path, CLOUD_NAME_TO_JSON_SCHEMA_NAME[cloud]
        )

        for module_name, yaml_path, _ in module_info:
            with open(yaml_path) as f:
                module_registry_dict = yaml.load(f)

            json_schema = _get_module_json(module_name, dirname(yaml_path))

            new_json_schema = deepcopy(json_schema)
            new_json_schema["$id"] = f"https://app.runx.dev/modules/{module_name}"
            new_json_schema["type"] = "object"
            REQUIRED_FIELDS = ["description", "properties"]
            if any(p not in json_schema for p in REQUIRED_FIELDS):
                missing_fields = [
                    field for field in REQUIRED_FIELDS if field not in json_schema
                ]
                raise Exception(
                    f"JSON schema for module {module_name} missing field(s): {missing_fields}"
                )

            if cloud == "common":
                module_aliases = []
            else:
                module_aliases = [
                    k for k, v in index_yaml["module_aliases"].items() if v == module_name
                ]

            module_display_name = (
                module_aliases[-1] if len(module_aliases) > 0 else module_name
            )

            new_json_schema["properties"]["type"] = {
                "description": "The name of this module",
                "enum": [module_name] + module_aliases,
                "default": module_display_name,
                "type": "string",
            }

            module_inputs = module_registry_dict["inputs"]
            for i in module_registry_dict["inputs"]:
                if i["user_facing"]:
                    input_name = i["name"]
                    if input_name not in json_schema["properties"]:
                        raise Exception(
                            f"property {input_name} is missing from json schema for module {module_name}"
                        )

                    type_definition_fields = ["type", "$ref", "oneOf", "anyOf"]
                    if all(
                        t not in json_schema["properties"][input_name]
                        for t in type_definition_fields
                    ):
                        raise Exception(
                            f"property *{input_name}* in json schema for module *{module_name}* is missing a type definition field. It should have one of the following fields: type, $ref, oneOf, anyOf"
                        )

                    if (
                        "default" in json_schema["properties"][input_name]
                        and "enum" in json_schema["properties"][input_name]
                    ):
                        if (
                            json_schema["properties"][input_name]["default"]
                            not in json_schema["properties"][input_name]["enum"]
                        ):
                            raise Exception(
                                f"property *{input_name}* in json schema for module *{module_name}* has a default value that is not in the enum list"
                            )

                    new_input_property_dict = new_json_schema["properties"][input_name]

                    new_input_property_dict["description"] = i["description"]
                    if "default" in i and i["default"] is not None:
                        new_input_property_dict["default"] = i["default"]
                    if "default" in new_input_property_dict and i["default"] is None:
                        del new_input_property_dict["default"]

            new_json_schema["required"] = [
                i["name"]
                for i in module_inputs
                if i["user_facing"] and "required=False" not in i["validator"]
            ] + ["type"]

            tags = []
            datastores = ["redis", "postgres", "documentdb", "mysql"]
            if any(d in module_name for d in datastores):
                tags.append("datastore")

            new_json_schema["opta_metadata"] = {
                "module_type": CONFIG_TYPE_ENV
                if module_registry_dict["environment_module"]
                else CONFIG_TYPE_SERVICE,
                "clouds": json_schema["opta_metadata"]["clouds"],
                "name": module_name,
                "display_name": module_display_name,
                "tags": tags,
            }

            if write:
                json_schema_file_path = _get_json_schema_module_path(
                    module_name, dirname(yaml_path)
                )
                with open(json_schema_file_path, "w") as f:
                    del new_json_schema["name"]
                    json.dump(new_json_schema, f, indent=2)
            else:
                if not _deep_equals(new_json_schema, json_schema):
                    raise Exception(
                        f"Module {module_name}'s json schema file seems to be out of date. Rerun this script with the --write flag to fix this."
                    )


def check_schemas(write: bool = False) -> None:
    print("checking module schemas...")
    _check_module_schemas(write)
    print("checking config schemas...")
    _check_opta_config_schemas(write)
