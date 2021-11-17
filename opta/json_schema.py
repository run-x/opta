import json
from copy import deepcopy
from os import listdir
from os.path import dirname, exists, isfile, join

from ruamel.yaml import YAML

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util

registry_path = join(dirname(dirname(__file__)), "config", "registry")
module_schemas_path = join(
    dirname(dirname(__file__)), "config", "registry", "schemas", "modules"
)

FOLDER_NAME_TO_CLOUD_LIST = {
    "aws": ["aws"],
    "azurerm": ["azure"],
    "google": ["gcp"],
    "common": ["aws", "azure", "gcp"],
}


def check_json_schema(write: bool = False) -> None:
    for cloud in ["aws", "azurerm", "google", "common"]:
        cloud_path = join(registry_path, cloud)
        module_path = join(cloud_path, "modules")
        module_names = [
            f.split(".")[0]
            for f in listdir(module_path)
            if isfile(join(module_path, f)) and f.endswith("yaml")
        ]

        for module_name in module_names:
            module_registry_dict = yaml.load(
                open(join(module_path, f"{module_name}.yaml"))
            )
            json_schema_file_path = join(module_schemas_path, f"{module_name}.json")

            if not exists(json_schema_file_path):
                raise Exception(
                    f"No JSON Schema file detected for module {module_name}. Please create a file named {module_name}.json in the config/registry/schemas/modules"
                )

            json_schema_file = open(json_schema_file_path)
            json_schema = json.load(json_schema_file)

            new_json_schema = deepcopy(json_schema)

            REQUIRED_FIELDS = ["description", "properties"]
            if "properties" not in json_schema:
                missing_fields = [
                    field for field in REQUIRED_FIELDS if field not in json_schema
                ]
                raise Exception(
                    f"JSON schema at {json_schema_file_path} missing {missing_fields} field(s)"
                )

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
            ]

            new_json_schema["opta_metadata"] = {
                "module_type": "environment"
                if module_registry_dict["environment_module"]
                else "service",
                "clouds": FOLDER_NAME_TO_CLOUD_LIST[cloud],
            }

            if write:
                with open(json_schema_file_path, "w") as f:
                    json.dump(new_json_schema, f, indent=2)
            else:
                if json.dumps(json_schema) != json.dumps(new_json_schema):
                    raise Exception(
                        f"Module {module_name}'s json schema file seems to be out of date. Rerun this script with the --write flag to fix this."
                    )
