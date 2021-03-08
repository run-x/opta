from collections.abc import Mapping
from os import path
from typing import Any, List

import click
import yamale
from yamale.validators import DefaultValidators, Validator

from opta.constants import schema_dir_path


class Module(Validator):
    """Custom Module Validator"""

    tag = "module"
    constraints: List = []

    # Yamale expects this function to return an array of errors
    def validate(self, value: Any) -> List[str]:
        if not isinstance(value, Mapping):
            return ["module is not a Map"]

        if "type" not in value:
            return ["module must have a 'type' field"]

        type = value["type"]
        module_schema_path = path.join(schema_dir_path, "modules", f"{type}.yaml")
        if not path.isfile(module_schema_path):
            return [f"{type} is not a valid module type"]

        module_schema = yamale.make_schema(module_schema_path)
        module_data = [(value, None)]
        return yamale.validate(module_schema, module_data, _raise_error=False).errors


validators = DefaultValidators.copy()
validators[Module.tag] = Module
main_schema_path = path.join(schema_dir_path, "opta.yaml")
main_schema = yamale.make_schema(main_schema_path, validators=validators)


def validate_yaml(config_file_path: str) -> None:
    data = yamale.make_data(config_file_path)
    yamale.validate(main_schema, data)


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
def validate(config: str) -> None:
    validate_yaml(config)
