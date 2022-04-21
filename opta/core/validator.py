from collections.abc import Mapping
from tempfile import NamedTemporaryFile
from typing import Any, List, Literal, Optional, Type

import yamale
from colored import attr, fg
from yamale.validators import DefaultValidators, Validator

from opta.constants import REGISTRY
from opta.exceptions import UserErrors
from opta.utils import yaml


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

        if self.cloud is None:
            raise Exception("Cloud needs to be specified for validation")

        type: str = value["type"]
        if type in REGISTRY[self.cloud]["module_aliases"]:
            value["type"] = REGISTRY[self.cloud]["module_aliases"][type]  # type: ignore
            type = value["type"]
        elif type not in REGISTRY[self.cloud]["modules"]:
            raise UserErrors(f"Module {type} is not supported for cloud {self.cloud}")
        module_schema_dicts = REGISTRY[self.cloud]["modules"][type]["validators"]
        with NamedTemporaryFile(mode="w") as f:
            yaml.dump_all(module_schema_dicts, f)
            f.flush()
            return _get_yamale_errors(value, f.name)


class AwsModule(Module):
    cloud = "aws"


class GcpModule(Module):
    cloud = "google"


class AzureModule(Module):
    cloud = "azurerm"


class LocalModule(Module):
    cloud = "local"


class HelmModule(Module):
    cloud = "helm"


class Opta(Validator):
    """Opta Yaml Validator"""

    tag = "opta"
    constaints: List = []
    extra_validators: List[Type[Validator]] = []
    environment_schema_dict: Optional[dict] = None
    service_schema_dicts: Optional[List[dict]] = None

    def _is_valid(self, value: Any) -> bool:
        if not isinstance(value, Mapping):
            return False
        return "org_name" in value or "name" in value

    def validate(self, value: Any) -> List[str]:
        if not isinstance(value, Mapping):
            return ["opta.yaml files should be a map"]

        if "org_name" in value:
            if self.environment_schema_dict is None:
                raise UserErrors(
                    "We currently only support AWS, GCP, and Azure and Local"
                )
            schema_dicts = [self.environment_schema_dict]
        else:
            if self.service_schema_dicts is None:
                raise UserErrors("We currently only support AWS, GCP, and Azure")
            schema_dicts = self.service_schema_dicts

        with NamedTemporaryFile(mode="w") as f:
            yaml.dump_all(schema_dicts, f)
            f.flush()
            return _get_yamale_errors(value, f.name, self.extra_validators)


class AwsId(Validator):
    tag = "aws_id"

    def _is_valid(self, value: Any) -> bool:
        str_value = str(value)

        return str_value.isdigit()


class AwsOpta(Opta):
    extra_validators = [AwsModule, AwsId]
    environment_schema_dict = REGISTRY["aws"]["validator"]
    service_schema_dicts = REGISTRY["aws"]["service_validator"]


class GcpOpta(Opta):
    extra_validators = [GcpModule]
    environment_schema_dict = REGISTRY["google"]["validator"]
    service_schema_dicts = REGISTRY["google"]["service_validator"]


class AureOpta(Opta):
    extra_validators = [AzureModule]
    environment_schema_dict = REGISTRY["azurerm"]["validator"]
    service_schema_dicts = REGISTRY["azurerm"]["service_validator"]


class LocalOpta(Opta):
    extra_validators = [LocalModule]
    environment_schema_dict = REGISTRY["local"]["validator"]
    service_schema_dicts = REGISTRY["local"]["service_validator"]


class HelmOpta(Opta):
    extra_validators = [HelmModule]
    environment_schema_dict = REGISTRY["helm"]["validator"]
    service_schema_dicts = REGISTRY["helm"]["service_validator"]


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
local_validators = DefaultValidators.copy()
local_validators[LocalOpta.tag] = LocalOpta
helm_validators = DefaultValidators.copy()
helm_validators[HelmOpta.tag] = HelmOpta

with NamedTemporaryFile(mode="w") as f:
    yaml.dump(REGISTRY["validator"], f)
    f.flush()
    vanilla_main_schema = yamale.make_schema(
        f.name, validators=vanilla_validators, parser="ruamel"
    )
    aws_main_schema = yamale.make_schema(
        f.name, validators=aws_validators, parser="ruamel"
    )
    gcp_main_schema = yamale.make_schema(
        f.name, validators=gcp_validators, parser="ruamel"
    )
    azure_main_schema = yamale.make_schema(
        f.name, validators=azure_validators, parser="ruamel"
    )
    local_main_schema = yamale.make_schema(
        f.name, validators=local_validators, parser="ruamel"
    )
    helm_main_schema = yamale.make_schema(
        f.name, validators=helm_validators, parser="ruamel"
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


def validate_yaml(
    config_file_path: str, cloud: str, json_schema: bool = False
) -> Literal[True]:
    if json_schema:
        print("TODO")
    else:
        CLOUD_TO_SCHEMA = {
            "aws": aws_main_schema,
            "google": gcp_main_schema,
            "azurerm": azure_main_schema,
            "local": local_main_schema,
            "helm": helm_main_schema,
        }
        DEFAULT_SCHEMA = vanilla_main_schema
        data = yamale.make_data(config_file_path, parser="ruamel")
        schema = CLOUD_TO_SCHEMA.get(cloud, DEFAULT_SCHEMA)
        yamale_result = yamale.validate(schema, data, _raise_error=False)
        errors = []
        for result in yamale_result:
            errors.extend(result.errors)

        if len(errors) > 0:
            _print_errors(errors)
            raise UserErrors(f"{config_file_path} is not a valid Opta file.")

    return True
