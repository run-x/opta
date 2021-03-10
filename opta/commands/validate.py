from collections.abc import Mapping
from os import path
from typing import Any, List, Literal

import click
import yamale
from colored import attr, fg
from yamale.validators import DefaultValidators, Validator

from opta.constants import schema_dir_path
from opta.exceptions import UserErrors


def _get_yamale_errors(data: Any, schema_path: str) -> List[str]:
    validators = DefaultValidators.copy()
    validators[Module.tag] = Module

    schema = yamale.make_schema(schema_path, validators=validators)
    formatted_data = [(data, None)]

    # This is an array of `ValidationResult`s, each of which has an
    # array of errors in its `errors` field
    validation_results = yamale.validate(schema, formatted_data, _raise_error=False)
    all_errors = []
    for result in validation_results:
        all_errors.extend(result.errors)

    return all_errors


class Opta(Validator):
    """Opta Yaml Validator"""

    tag = "opta"
    constaints: List = []

    def _is_valid(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return False
        return "org_name" in value or "name" in value

    def validate(self, value: Any) -> List[str]:
        if not isinstance(value, Mapping):
            return ["opta.yaml files should be a map"]

        if "org_name" in value:
            schema_path = path.join(schema_dir_path, "environment.yaml")
        else:
            schema_path = path.join(schema_dir_path, "service.yaml")

        return _get_yamale_errors(value, schema_path)


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

        return _get_yamale_errors(value, module_schema_path)


validators = DefaultValidators.copy()
validators[Opta.tag] = Opta

main_schema_path = path.join(schema_dir_path, "opta.yaml")
main_schema = yamale.make_schema(main_schema_path, validators=validators)


def _print_success(config_file_path: str) -> None:
    print(fg("green"), end="")
    print(attr("bold"), end="")
    print(f"{config_file_path} is a valid opta file!")
    print(attr("reset"), end="")


def _print_errors(errors: List[str]) -> None:
    print(fg("red"), end="")
    print(attr("bold"), end="")
    print("Opta file validation failed with errors:")
    print(attr("reset"), end="")

    print(fg("red"), end="")
    for error in errors:
        print(f"  {error}")
    print(attr("reset"), end="")


def validate_yaml(config_file_path: str) -> Literal[True]:
    data = yamale.make_data(config_file_path)
    yamale_result = yamale.validate(main_schema, data, _raise_error=False)
    errors = []
    for result in yamale_result:
        errors.extend(result.errors)

    if len(errors) == 0:
        _print_success(config_file_path)
    else:
        _print_errors(errors)
        raise UserErrors(f"{config_file_path} is not a valid Opta file.")

    return True


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
def validate(config: str) -> None:
    validate_yaml(config)
