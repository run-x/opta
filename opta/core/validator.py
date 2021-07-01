from collections.abc import Mapping
from os import path
from typing import Any, List, Literal, Optional, Type

import yamale
from colored import attr, fg
from yamale.validators import DefaultValidators, Validator

from opta.constants import REGISTRY, schema_dir_path
from opta.exceptions import UserErrors


class Module(Validator):
    """Custom Module Validator"""

    tag = "module"
    constraints: List = []
    cloud: Optional[str] = None

    # Yamale expects this function to return an array of errors
    def validate(self, value: Any) -> List[str]:
        if not isinstance(value, Mapping):
            return ["module is not a Map"]

        if "type" not in value:
            return ["module must have a 'type' field"]

        type = value["type"]
        if "alias" in REGISTRY["modules"].get(type, {}):
            if self.cloud is None or self.cloud not in REGISTRY["modules"][type]["alias"]:
                raise UserErrors(
                    f"Alias module is unsupported-- assumed cloud is {self.cloud}, supported alias for clouds is "
                    f"{list(REGISTRY['modules'][type]['alias'].keys())}"
                )
            value["type"] = REGISTRY["modules"][type]["alias"][self.cloud]  # type:ignore
            type = value["type"]
        elif REGISTRY["modules"].get(type, {}).get("cloud", "") not in {
            "any",
            self.cloud,
        }:
            raise UserErrors(f"Module {type} is not supported for cloud {self.cloud}")
        module_schema_path = path.join(schema_dir_path, "modules", f"{type}.yaml")
        if not path.isfile(module_schema_path):
            return [f"{type} is not a valid module type"]

        return _get_yamale_errors(value, module_schema_path)


class AwsModule(Module):
    cloud = "aws"


class GcpModule(Module):
    cloud = "google"


class AzureModule(Module):
    cloud = "azurerm"


class Opta(Validator):
    """Opta Yaml Validator"""

    tag = "opta"
    constaints: List = []
    extra_validators: List[Type[Validator]] = []
    environment_schema_path: Optional[str] = None

    def _is_valid(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return False
        return "org_name" in value or "name" in value

    def validate(self, value: Any) -> List[str]:
        if not isinstance(value, Mapping):
            return ["opta.yaml files should be a map"]

        if "org_name" in value:
            if self.environment_schema_path is None:
                raise UserErrors("We currently only support AWS, GCP, and Azure")
            schema_path = self.environment_schema_path
        else:
            schema_path = path.join(schema_dir_path, "service.yaml")

        return _get_yamale_errors(value, schema_path, self.extra_validators)


class AwsId(Validator):
    tag = "aws_id"

    def _is_valid(self, value: Any) -> bool:
        str_value = str(value)

        return str_value.isdigit()


class AwsOpta(Opta):
    extra_validators = [AwsModule, AwsId]
    environment_schema_path = path.join(schema_dir_path, "aws_environment.yaml")


class GcpOpta(Opta):
    extra_validators = [GcpModule]
    environment_schema_path = path.join(schema_dir_path, "gcp_environment.yaml")


class AureOpta(Opta):
    extra_validators = [AzureModule]
    environment_schema_path = path.join(schema_dir_path, "azure_environment.yaml")


def _get_yamale_errors(
    data: Any, schema_path: str, extra_validators: Optional[List[Type[Validator]]] = None
) -> List[str]:
    extra_validators = extra_validators or []
    validators = DefaultValidators.copy()
    for validator in extra_validators:
        validators[validator.tag] = validator

    schema = yamale.make_schema(schema_path, validators=validators, parser="ruamel")
    formatted_data = [(data, None)]

    # This is an array of `ValidationResult`s, each of which has an
    # array of errors in its `errors` field
    validation_results = yamale.validate(schema, formatted_data, _raise_error=False)
    all_errors = []
    for result in validation_results:
        all_errors.extend(result.errors)

    return all_errors


vanilla_validators = DefaultValidators.copy()
vanilla_validators[Opta.tag] = Opta
aws_validators = DefaultValidators.copy()
aws_validators[AwsOpta.tag] = AwsOpta
gcp_validators = DefaultValidators.copy()
gcp_validators[GcpOpta.tag] = GcpOpta
azure_validators = DefaultValidators.copy()
azure_validators[AureOpta.tag] = AureOpta

main_schema_path = path.join(schema_dir_path, "opta.yaml")
vanilla_main_schema = yamale.make_schema(
    main_schema_path, validators=vanilla_validators, parser="ruamel"
)
aws_main_schema = yamale.make_schema(
    main_schema_path, validators=aws_validators, parser="ruamel"
)
gcp_main_schema = yamale.make_schema(
    main_schema_path, validators=gcp_validators, parser="ruamel"
)
azure_main_schema = yamale.make_schema(
    main_schema_path, validators=azure_validators, parser="ruamel"
)


def _print_errors(errors: List[str]) -> None:
    print(fg("red"), end="")
    print(attr("bold"), end="")
    print("Opta file validation failed with errors:")
    print(attr("reset"), end="")

    print(fg("red"), end="")
    for error in errors:
        print(f"  {error}")
    print(attr("reset"), end="")


def validate_yaml(config_file_path: str, cloud: str) -> Literal[True]:
    data = yamale.make_data(config_file_path, parser="ruamel")
    if cloud == "aws":
        yamale_result = yamale.validate(aws_main_schema, data, _raise_error=False)
    elif cloud == "google":
        yamale_result = yamale.validate(gcp_main_schema, data, _raise_error=False)
    elif cloud == "azurerm":
        yamale_result = yamale.validate(azure_main_schema, data, _raise_error=False)
    else:
        yamale_result = yamale.validate(vanilla_main_schema, data, _raise_error=False)
    errors = []
    for result in yamale_result:
        errors.extend(result.errors)

    if len(errors) > 0:
        _print_errors(errors)
        raise UserErrors(f"{config_file_path} is not a valid Opta file.")

    return True
