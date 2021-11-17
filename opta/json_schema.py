import json
from os import listdir
from os.path import dirname, isfile, join

from ruamel.yaml import YAML

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util

registry_path = join(dirname(dirname(__file__)), "config", "registry")
module_schemas_path = join(
    dirname(dirname(__file__)), "config", "registry", "schemas", "modules"
)


def generate_json_schema() -> None:
    for cloud in ["aws", "azurerm", "google"]:
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
            json_schema_file = open(json_schema_file_path, "w")
            json_schema = json.load(json_schema_file)

            if "properties" in json_schema:
                for i in module_registry_dict["inputs"]:
                    if i["user_facing"]:
                        input_name = i["name"]
                        if input_name not in json_schema["properties"]:
                            raise Exception(
                                f"property {input_name} is missing from json schema for module {module_name}"
                            )
                        input_property_dict = json_schema["properties"][input_name]
                        input_property_dict["description"] = i["description"]

            # json.dumps(json_schema, json_schema_file, indent=True)
