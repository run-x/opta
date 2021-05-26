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


class Opta(Validator):
    """Opta Yaml Validator"""

    tag = "opta"
    constaints: List = []
    module_validator: Optional[Type[Module]] = None
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
                raise UserErrors("We currently only support AWS and GCP")
            schema_path = self.environment_schema_path
        else:
            schema_path = path.join(schema_dir_path, "service.yaml")

        return _get_yamale_errors(value, schema_path, self.module_validator)


class AwsOpta(Opta):
    module_validator = AwsModule
    environment_schema_path = path.join(schema_dir_path, "aws_environment.yaml")


class GcpOpta(Opta):
    module_validator = GcpModule
    environment_schema_path = path.join(schema_dir_path, "gcp_environment.yaml")


class AwsId(Validator):
    tag = "aws_id"

    def _is_valid(self, value: Any) -> bool:
        # import pdb
        #
        # pdb.set_trace()
        return True


def _get_yamale_errors(
    data: Any, schema_path: str, module_validator: Any = None
) -> List[str]:
    validators = DefaultValidators.copy()
    if module_validator is not None:
        validators[module_validator.tag] = module_validator

    schema = yamale.make_schema(schema_path, validators=validators)
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
aws_validators[AwsId.tag] = AwsId
gcp_validators = DefaultValidators.copy()
gcp_validators[GcpOpta.tag] = GcpOpta

main_schema_path = path.join(schema_dir_path, "opta.yaml")
vanilla_main_schema = yamale.make_schema(main_schema_path, validators=vanilla_validators)
aws_main_schema = yamale.make_schema(main_schema_path, validators=aws_validators)
gcp_main_schema = yamale.make_schema(main_schema_path, validators=gcp_validators)


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


def validate_yaml(config_file_path: str, cloud: str) -> Literal[True]:
    data = yamale.make_data(config_file_path)
    if cloud == "aws":
        yamale_result = yamale.validate(aws_main_schema, data, _raise_error=False)
    elif cloud == "google":
        yamale_result = yamale.validate(gcp_main_schema, data, _raise_error=False)
    else:
        yamale_result = yamale.validate(vanilla_main_schema, data, _raise_error=False)
    errors = []
    for result in yamale_result:
        errors.extend(result.errors)

    if len(errors) == 0:
        _print_success(config_file_path)
    else:
        _print_errors(errors)
        raise UserErrors(f"{config_file_path} is not a valid Opta file.")

    return True
