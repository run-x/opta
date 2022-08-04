from __future__ import annotations

import hashlib
import importlib
import os
import re
import shutil
import tempfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, TypedDict

import boto3
import click
import google.auth.transport.requests
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from botocore.exceptions import ClientError, NoCredentialsError
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION

from modules.base import ModuleProcessor
from opta.constants import GENERATED_KUBE_CONFIG_DIR, REGISTRY, VERSION
from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.core.helm_cloud_client import HelmCloudClient
from opta.core.local import Local
from opta.core.validator import validate_yaml
from opta.crash_reporter import CURRENT_CRASH_REPORTER
from opta.exceptions import UserErrors
from opta.input_variable import InputVariable
from opta.module import Module
from opta.plugins.derived_providers import DerivedProviders
from opta.utils import (
    check_opta_file_exists,
    deep_merge,
    hydrate,
    logger,
    multi_from_dict,
    yaml,
)
from opta.utils.dependencies import ensure_installed, validate_installed_path_executables

PROCESSOR_DICT: Dict[str, str] = {
    "aws-base": "AwsBaseProcessor",
    "aws-k8s-service": "AwsK8sServiceProcessor",
    "aws-k8s-base": "AwsK8sBaseProcessor",
    "datadog": "DatadogProcessor",
    "gcp-k8s-base": "GcpK8sBaseProcessor",
    "gcp-k8s-service": "GcpK8sServiceProcessor",
    "gcp-gke": "GcpGkeProcessor",
    "aws-dns": "AwsDnsProcessor",
    "aws-postgres": "AwsPostgresProcessor",
    "aws-documentdb": "AwsDocumentDbProcessor",
    "helm-chart": "HelmChartProcessor",
    "aws-iam-role": "AwsIamRoleProcessor",
    "aws-iam-user": "AwsIamUserProcessor",
    "aws-eks": "AwsEksProcessor",
    "aws-ses": "AwsEmailProcessor",
    "aws-sqs": "AwsSqsProcessor",
    "aws-sns": "AwsSnsProcessor",
    "aws-nodegroup": "AwsNodegroup",
    "azure-base": "AzureBaseProcessor",
    "azure-k8s-base": "AzureK8sBaseProcessor",
    "azure-k8s-service": "AzureK8sServiceProcessor",
    "local-k8s-service": "LocalK8sServiceProcessor",
    "external-ssl-cert": "ExternalSSLCert",
    "aws-s3": "AwsS3Processor",
    "gcp-dns": "GCPDnsProcessor",
    "gcp-service-account": "GcpServiceAccountProcessor",
    "custom-terraform": "CustomTerraformProcessor",
    "aws-dynamodb": "AwsDynamodbProcessor",
    "mongodb-atlas": "MongodbAtlasProcessor",
    "cloudfront-distribution": "CloudfrontDistributionProcessor",
    "lambda-function": "LambdaFunctionProcessor",
    "k8s-manifest": "K8smanifestProcessor",
    "azure-aks": "AzureAksProcessor",
    "global-accelerator": "GlobalAcceleratorsProcessor",
    "aws-vpn": "AwsVPNProcessor",
}


# Relies on the python file being module_some_name.py, and then
# the opta module file being named module-some-name
def generate_pymodule_path(module_type: str) -> str:
    base_name = "_".join(module_type.split("-"))
    return ".".join(["modules", base_name, base_name])


def get_processor_class(module_type: str) -> ModuleProcessor:
    try:
        pymodule_path = generate_pymodule_path(module_type)
        pymodule = importlib.import_module(pymodule_path)
    except ModuleNotFoundError:
        return ModuleProcessor

    return pymodule.__dict__[PROCESSOR_DICT[module_type]]


class StructuredDefault(TypedDict):
    input_name: str
    default: Any
    force_update_default_counter: int


class StructuredConfig(TypedDict):
    opta_version: str
    date: str
    original_spec: str
    defaults: Dict[str, List[StructuredDefault]]


class Layer:
    def __init__(
        self,
        name: str,
        org_name: Optional[str],
        providers: Dict[Any, Any],
        modules_data: List[Any],
        path: str,
        parent: Optional[Layer] = None,
        variables: Optional[Dict[str, Any]] = None,
        original_spec: str = "",
        stateless_mode: bool = False,
    ):
        if not Layer.valid_name(name):
            raise UserErrors(
                "Invalid layer, can only contain letters, dashes and numbers!"
            )
        self.name = name
        self.original_spec = original_spec
        self.parent = parent
        self.path = path
        self.cloud: str
        if parent is None:
            if len(providers) == 0:
                # no parent, no provider = we are in helm (byok) mode
                self.cloud = "helm"
                # read the provider from the registry instead - the opta file doesn't define any with byok
                providers = REGISTRY[self.cloud]["output_providers"]
            elif org_name is None:
                raise UserErrors(
                    "Config must have org name or a parent who has an org name"
                )
        self.org_name = org_name
        if self.parent and self.org_name is None:
            self.org_name = self.parent.org_name
        self.providers = providers
        total_base_providers = deep_merge(
            self.providers, self.parent.providers if self.parent else {}
        )
        if "google" in total_base_providers and "aws" in total_base_providers:
            raise UserErrors(
                "You can have AWS as the cloud provider, or google, but not both"
            )
        if "google" in total_base_providers:
            self.cloud = "google"
        elif "aws" in total_base_providers:
            self.cloud = "aws"
        elif "azurerm" in total_base_providers:
            self.cloud = "azurerm"
        elif "local" in total_base_providers:
            self.cloud = "local"

        if not hasattr(self, "cloud"):
            raise UserErrors(
                "No cloud provider (AWS, GCP, or Azure) found, \n"
                + " or did you miss providing the --local flag for local deployment?"
            )
        self.variables = variables or {}
        self.modules: List[Module] = []
        for module_data in modules_data:
            self.modules.append(Module(self, module_data, self.parent,))
        module_names: set = set()
        for module in self.modules:
            if module.name in module_names:
                raise UserErrors(
                    f"The module name {module.name} is used multiple time in the "
                    "layer. Module names must be unique per layer"
                )
            module_names.add(module.name)
        self.stateless_mode = stateless_mode

    def get_cluster_name(self) -> str:
        return f"opta-{self.root().name}"

    def get_kube_config_file_name(self) -> str:
        config_file_name = (
            f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{self.root().name}-{self.cloud}.yaml"
        )
        return config_file_name

    def get_cloud_client(self) -> CloudClient:
        if self.cloud == "aws":
            return AWS(self)
        elif self.cloud == "google":
            return GCP(self)
        elif self.cloud == "azurerm":
            return Azure(self)
        elif self.cloud == "local":
            return Local(self)
        elif self.cloud == "helm":
            return HelmCloudClient(self)
        else:
            raise Exception(
                f"Unknown cloud {self.cloud}. Can not handle getting the cloud client"
            )

    @classmethod
    def load_from_yaml(
        cls,
        config: str,
        env: Optional[str],
        is_parent: bool = False,
        local: bool = False,
        json_schema: bool = False,
        stateless_mode: bool = False,
        input_variables: Optional[Dict[str, str]] = None,
        strict_input_variables: bool = True,
    ) -> Layer:
        t = None
        if config.startswith("git@"):
            logger.debug("Loading layer from git...")
            git_url, file_path = config.split("//")
            branch = "main"
            if "?" in file_path:
                file_path, file_vars = file_path.split("?")
                res = dict(
                    map(
                        lambda x: (x.split("=")[0], x.split("=")[1]),
                        file_vars.split(","),
                    )
                )
                branch = res.get("ref", branch)
            t = tempfile.mkdtemp()
            # Clone into temporary dir
            try:
                import git
            except ImportError:
                raise UserErrors(
                    "Please install git locally to be able to load environments from git"
                )

            git.Repo.clone_from(git_url, t, branch=branch, depth=1)
            config_path = os.path.join(t, file_path)
        else:
            config_path = config

        # this will make sure that the file exist and support alternate y(a)ml extension
        config_path = check_opta_file_exists(config_path, prompt=False)

        with open(config_path) as f:
            config_string = f.read()
        logger.debug(f"Loaded the following configfile:\n{config_string}")
        conf = yaml.load(config_string)

        conf["original_spec"] = config_string
        conf["path"] = config_path

        layer = cls.load_from_dict(
            conf, env, is_parent, stateless_mode, input_variables, strict_input_variables
        )
        if local:
            pass
        validate_yaml(config_path, layer.cloud, json_schema)
        if t is not None:
            shutil.rmtree(t)

        cls.validate_layer(layer)
        if not is_parent:
            CURRENT_CRASH_REPORTER.set_layer(layer)
        return layer

    def structured_config(self) -> StructuredConfig:
        return {
            "opta_version": VERSION,
            "date": datetime.utcnow().isoformat(),
            "original_spec": self.original_spec,
            "defaults": {module.name: module.used_defaults for module in self.modules},
        }

    @classmethod
    def load_from_dict(
        cls,
        conf: Dict[Any, Any],
        env: Optional[str],
        is_parent: bool = False,
        stateless_mode: bool = False,
        input_variables: Optional[Dict[str, str]] = None,
        strict_input_variables: bool = True,
    ) -> Layer:
        input_variables = input_variables or {}
        # Handle input variables
        expected_input_variables = multi_from_dict(InputVariable, conf, "input_variables")
        current_variables = InputVariable.render_dict(
            expected_input_variables, input_variables, strict_input_variables
        )
        modules_data = conf.get("modules", [])
        environments = conf.pop("environments", None)
        original_spec = conf.pop("original_spec", "")
        path = conf["path"]
        name = conf.pop("name", None)
        if name is None:
            raise UserErrors("Config must have name")
        if is_parent and environments is not None:
            raise UserErrors(
                f"Environment {name} can not have an environment itself (usually this means your file is "
                "self-referencing as it's own parent)."
            )
        org_name = conf.pop("org_name", None)
        providers = conf.pop("providers", {})
        _validate_providers(providers)
        if "aws" in providers:
            providers["aws"]["account_id"] = providers["aws"].get("account_id", "")
            account_id = str(providers["aws"]["account_id"])
            account_id = "0" * (12 - len(account_id)) + account_id
            providers["aws"]["account_id"] = account_id
        if environments:
            potential_envs: Dict[str, Tuple] = {}
            for env_meta in environments:
                env_name = env_meta["name"]
                parent_path: str = env_meta["path"]
                if not parent_path.startswith("git@") and not parent_path.startswith("/"):
                    parent_path = os.path.join(os.path.dirname(path), env_meta["path"])
                current_parent = cls.load_from_yaml(
                    parent_path, None, is_parent=True, stateless_mode=stateless_mode
                )
                if current_parent.parent is not None:
                    raise UserErrors(
                        "A parent can not have a parent, only one level of parent-child allowed."
                    )
                current_env = current_parent.get_env()
                if current_env in potential_envs.keys():
                    raise UserErrors(
                        f"Same environment: {current_env} is imported twice as parent"
                    )
                if current_parent.name == name:
                    raise UserErrors(
                        "A service can not have the same name as its environment."
                    )
                potential_envs[env_name] = (current_parent, env_meta)

            if env is None:
                if len(potential_envs) == 1:
                    env = list(potential_envs.keys())[0]
                else:
                    """This is a repeatable prompt, which will not disappear until a valid choice is provided or SIGABRT
                    is given."""
                    env = click.prompt(
                        "Choose an Environment for the Given set of choices",
                        type=click.Choice([x for x in potential_envs.keys()]),
                    )
            elif env not in potential_envs:
                raise UserErrors(
                    f"Invalid --env flag, valid ones are {list(potential_envs.keys())}"
                )

            current_parent, env_meta = potential_envs[env]
            current_variables = deep_merge(
                current_variables, env_meta.get("variables", {})
            )
            current_variables = deep_merge(current_variables, env_meta.get("vars", {}))

            return cls(
                name,
                org_name,
                providers,
                modules_data,
                path,
                current_parent,
                current_variables,
                original_spec,
                stateless_mode,
            )
        return cls(
            name,
            org_name,
            providers,
            modules_data,
            path,
            variables=current_variables,
            original_spec=original_spec,
            stateless_mode=stateless_mode,
        )

    @classmethod
    def validate_layer(cls, layer: "Layer") -> None:
        # Check for Uniqueness of Modules
        unique_modules: Set[str] = set()
        for module in layer.modules:
            if module.desc.get("is_unique", False) and unique_modules.__contains__(
                module.type
            ):
                raise UserErrors(
                    f"Module Type: '{module.type}' used twice in the configuration. Please check and update as required."
                )
            unique_modules.add(module.type)

    @staticmethod
    def valid_name(name: str) -> bool:
        pattern = "^[A-Za-z0-9-]*$"
        return bool(re.match(pattern, name))

    def get_env(self) -> str:
        if self.parent is not None:
            return self.parent.get_env()
        return self.name

    def get_modules(self, module_idx: Optional[int] = None) -> List[Module]:
        module_idx = len(self.modules) - 1 if module_idx is None else module_idx
        return self.modules[0 : module_idx + 1]

    def get_module(
        self, module_name: str, module_idx: Optional[int] = None
    ) -> Optional[Module]:
        # TODO this code is duplicated everywhere
        module_idx = len(self.modules) - 1 if module_idx is None else module_idx
        for module in self.modules[0 : module_idx + 1]:
            if module.name == module_name:
                return module
        return None

    def get_required_path_dependencies(self) -> FrozenSet[str]:
        deps: Set[str] = set()
        for module in self.modules:
            module_deps = self.processor_for(module).required_path_dependencies
            deps |= module_deps

        return frozenset(deps)

    def validate_required_path_dependencies(self) -> None:
        deps = self.get_required_path_dependencies()
        validate_installed_path_executables(deps)

    def get_module_by_type(
        self, module_type: str, module_idx: Optional[int] = None
    ) -> list[Module]:
        module_idx = len(self.modules) - 1 if module_idx is None else module_idx
        modules = []
        for module in self.modules[0 : module_idx + 1]:
            if module.type == module_type or module.aliased_type == module_type:
                modules.append(module)
        return modules

    def outputs(self, module_idx: Optional[int] = None) -> Iterable[str]:
        ret: List[str] = []
        module_idx = len(self.modules) - 1 if module_idx is None else module_idx
        for module in self.modules[0 : module_idx + 1]:
            ret += module.outputs()
        if self.parent is None:
            ret.append("providers")
        return ret

    def gen_tf(
        self, module_idx: int, existing_config: Optional[StructuredConfig] = None
    ) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        for module in self.modules[0 : module_idx + 1]:
            self.processor_for(module).process(module_idx)

        for module in self.modules[0 : module_idx + 1]:
            output_prefix = (
                None if len(self.get_module_by_type(module.type)) == 1 else module.name
            )
            existing_defaults: Optional[List[StructuredDefault]] = None
            if existing_config is not None:
                existing_defaults = existing_config.get("defaults", {}).get(module.name)
            ret = deep_merge(
                module.gen_tf(
                    output_prefix=output_prefix, existing_defaults=existing_defaults,
                ),
                ret,
            )
        ret["output"] = ret.get("output", {})
        if self.parent is None:
            ret["output"]["providers"] = {"value": self.providers}
        ret["output"]["state_storage"] = {"value": self.state_storage()}

        return hydrate(ret, self.metadata_hydration())

    def pre_hook(self, module_idx: int) -> None:
        for module in self.modules[0 : module_idx + 1]:
            self.processor_for(module).pre_hook(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        for module in self.modules[0 : module_idx + 1]:
            self.processor_for(module).post_hook(module_idx, exception)

    def post_delete(self, module_idx: int) -> None:
        module = self.modules[module_idx]
        logger.debug(f"Running post delete for module {module.name}")
        self.processor_for(module).post_delete(module_idx)

    def processor_for(self, module: Module) -> ModuleProcessor:
        module_type = module.aliased_type or module.type
        processor_class = get_processor_class(module_type)
        return processor_class(module, self)

    def metadata_hydration(self) -> Dict[Any, Any]:
        parent_name = self.parent.name if self.parent is not None else "nil"
        parent = None
        if self.parent is not None:
            parent = SimpleNamespace(
                **{
                    k: f"${{data.terraform_remote_state.parent.outputs.{k}}}"
                    for k in self.parent.outputs()
                }
            )
        providers = self.providers
        if self.parent is not None:
            providers = deep_merge(providers, self.parent.providers)
        provider_hydration = {}
        for name, values in providers.items():
            provider_hydration[name] = SimpleNamespace(**values)

        region: Optional[str] = None
        k8s_access_token = None
        if self.cloud == "google":
            gcp = GCP(self)
            region = gcp.region
            credentials = gcp.get_credentials()[0]
            if isinstance(credentials, service_account.Credentials):
                service_account_credentials: service_account.Credentials = (
                    credentials.with_scopes(
                        [
                            "https://www.googleapis.com/auth/userinfo.email",
                            "https://www.googleapis.com/auth/cloud-platform",
                        ]
                    )
                )
                service_account_credentials.refresh(
                    google.auth.transport.requests.Request()
                )
                k8s_access_token = service_account_credentials.token
            else:
                k8s_access_token = credentials.token
            if k8s_access_token is None:
                raise Exception("Was unable to get GCP access token")
        elif self.cloud == "aws":
            aws = AWS(self)
            region = aws.region
        elif self.cloud == "azurerm":
            region = self.root().providers["azurerm"]["location"]
        elif self.cloud == "local":
            pass

        return {
            "parent": parent,
            "vars": SimpleNamespace(**self.variables),
            "variables": SimpleNamespace(**self.variables),
            "parent_name": parent_name,
            "layer_name": self.name,
            "state_storage": self.state_storage(),
            "env": self.get_env(),
            "kubeconfig": KUBE_CONFIG_DEFAULT_LOCATION,
            "k8s_access_token": k8s_access_token,
            "region": region,
            **provider_hydration,
        }

    def get_event_properties(self) -> Dict[str, Any]:
        current_keys: Dict[str, Any] = {}
        for module in self.modules:
            new_keys = self.processor_for(module).get_event_properties()
            for key, val in new_keys.items():
                current_keys[key] = current_keys.get(key, 0) + val
        current_keys["total_resources"] = sum([x for x in current_keys.values()])
        current_keys["org_name"] = self.org_name
        current_keys["layer_name"] = self.name
        current_keys["parent_name"] = self.parent.name if self.parent is not None else ""
        return current_keys

    @lru_cache(maxsize=None)
    def bucket_exists(self, bucket_name: str) -> bool:

        if self.is_stateless_mode() is True:
            return False

        if self.cloud == "aws":
            region = self.providers["aws"]["region"]
            return AWS(self).bucket_exists(bucket_name, region)
        elif self.cloud == "google":
            return GCP(self).bucket_exists(bucket_name)
        else:  # Note - this function does not work for Azure
            return False

    def _get_unique_hash(self) -> str:

        if self.cloud == "aws":
            provider = self.providers["aws"]
            str2hash = provider["region"] + provider["account_id"]
        elif self.cloud == "google":
            provider = self.providers["google"]
            str2hash = provider["region"] + provider["project"]
        elif self.cloud == "azurerm":
            provider = self.providers["azurerm"]
            str2hash = (
                provider["location"] + provider["tenant_id"] + provider["subscription_id"]
            )
        else:
            return ""
        return hashlib.md5(str2hash.encode("utf-8")).hexdigest()[0:4]  # nosec

    def state_storage(self) -> str:
        if self.cloud == "local":
            return os.path.join(str(Path.home()), ".opta", "local", "tfstate")
        elif self.cloud == "helm":
            return f"{self.org_name}-{self.name}"

        if self.parent is not None:
            return self.parent.state_storage()

        suffix = self._get_unique_hash()

        if self.cloud == "azurerm":
            name_hash = hashlib.md5(  # nosec
                f"{self.org_name}{self.name}".encode("utf-8")
            ).hexdigest()[0:16]
            return f"opta{name_hash}"  # For Azure, for now we don't add suffix
        else:
            orig_name = f"opta-tf-state-{self.org_name}-{self.name}"

        if self.bucket_exists(orig_name):
            return orig_name
        else:
            return orig_name + "-" + suffix

    def gen_providers(self, module_idx: int, clean: bool = True) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {"provider": {}}

        hydration = self.metadata_hydration()
        providers = self.providers
        if self.parent is not None:
            providers = deep_merge(providers, self.parent.providers)
        for cloud, provider in providers.items():
            provider = self.handle_special_providers(cloud, provider, clean)
            ret["provider"][cloud] = hydrate(provider, hydration)
            if cloud in REGISTRY:
                ret["terraform"] = hydrate(
                    {x: REGISTRY[cloud][x] for x in ["required_providers", "backend"]},
                    deep_merge(hydration, {"provider": provider}),
                )

                if self.parent is not None:
                    # Add remote state
                    backend, config = list(REGISTRY[cloud]["backend"].items())[0]
                    ret["data"] = {
                        "terraform_remote_state": {
                            "parent": {
                                "backend": backend,
                                "config": hydrate(
                                    config,
                                    {
                                        "layer_name": self.parent.name,
                                        "env": self.get_env(),
                                        "state_storage": self.state_storage(),
                                        "provider": self.parent.providers.get(cloud, {}),
                                        "region": hydration["region"],
                                        "k8s_access_token": hydration["k8s_access_token"],
                                    },
                                ),
                            }
                        }
                    }

        # Add derived providers like k8s from parent
        ret = deep_merge(
            ret,
            DerivedProviders(self.parent, is_parent=True).gen_tf(
                {
                    "region": hydration["region"],
                    "k8s_access_token": hydration["k8s_access_token"],
                }
            ),
        )
        # Add derived providers like k8s from own modules
        ret = deep_merge(
            ret,
            DerivedProviders(self, is_parent=False).gen_tf(
                {
                    "region": hydration["region"],
                    "k8s_access_token": hydration["k8s_access_token"],
                },
                module_idx=module_idx,
            ),
        )

        return ret

    # Special logic for mapping the opta config to the provider block
    def handle_special_providers(
        self, provider_name: str, provider_data: dict, clean: bool
    ) -> dict:
        new_provider_data = provider_data.copy()
        # Terraform requires an array of AWS account ids, but having the customer specify
        # that is awk, so transform it during the mapping.
        if provider_name == "aws" and "account_id" in new_provider_data:
            aws_account_id = new_provider_data.pop("account_id")
            new_provider_data["allowed_account_ids"] = [aws_account_id]

        if provider_name == "azurerm":
            new_provider_data["features"] = {
                "key_vault": {"purge_soft_delete_on_destroy": False}
            }

        # TODO(ankur): Very ugly
        if clean and provider_name == "azurerm":
            new_provider_data.pop("location")

        return new_provider_data

    # Get the root-most layer
    def root(self) -> "Layer":
        layer = self
        while layer.parent is not None:
            layer = layer.parent

        return layer

    def is_stateless_mode(self) -> bool:
        """is_stateless_mode returns True if this layer state is NOT managed by opta
        In most case, the state is managed by Opta, except for commands like `generate-terraform` where no remote state is needed

        Note: if this method is mocked and used in a condition it would be evaluated to True, to prevent this use `layer.is_stateless_mode() is True`
        """
        return self.stateless_mode

    def verify_cloud_credentials(self) -> None:
        if self.cloud == "aws":
            self._verify_aws_cloud_credentials()
        if self.cloud == "google":
            self._verify_gcp_cloud_credentials()
        if self.cloud == "azurerm":
            self._verify_azure_cloud_credentials()

    def _verify_azure_cloud_credentials(self) -> None:
        try:
            DefaultAzureCredential()
        except ClientAuthenticationError as e:
            raise UserErrors(
                "Azure Cloud are not configured properly.\n" f" Error: {e.message}"
            )

    def _verify_gcp_cloud_credentials(self) -> None:
        try:
            _, configured_project_id = default()
            required_project_id = self.root().providers["google"]["project"]
            if required_project_id != configured_project_id:
                raise UserErrors(
                    "\nSystem configured GCP Credentials are different from the ones being used in the "
                    "Configuration. \nSystem is configured with credentials for account "
                    f"{configured_project_id} but the config requires the credentials for "
                    f"{required_project_id}."
                )
        except DefaultCredentialsError:
            raise UserErrors(
                "Google Cloud credentials are not configured properly.\n"
                "Visit `https://googleapis.dev/python/google-api-core/latest/auth.html#overview` "
                "for more information."
            )

    def _verify_aws_cloud_credentials(self) -> None:
        ensure_installed("aws")
        try:
            aws_caller_identity = boto3.client("sts").get_caller_identity()
            configured_aws_account_id = aws_caller_identity["Account"]
            required_aws_account_id = self.root().providers["aws"]["account_id"]
            if required_aws_account_id != configured_aws_account_id:
                raise UserErrors(
                    "\nSystem configured AWS Credentials are different from the ones being used in the "
                    f"Configuration. \nSystem is configured with credentials for account "
                    f"{configured_aws_account_id} but the config requires the credentials for "
                    f"{required_aws_account_id}."
                )
        except NoCredentialsError:
            raise UserErrors(
                "Unable to locate credentials.\n"
                "Visit `https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html` "
                "for more information."
            )
        except ClientError as e:
            raise UserErrors(
                "The AWS Credentials are not configured properly.\n"
                f" - Code: {e.response['Error']['Code']} Error Message: {e.response['Error']['Message']}"
                "Visit `https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html` "
                "for more information."
            )


def _validate_providers(providers: dict) -> None:
    """
    Validates Configuration and throws Exception when providers section is provided but left Empty
    name: Test Name
    org_name: Test Org Name
    providers:
    modules:...
    """
    if providers is None:
        raise UserErrors(
            "Environment Configuration needs a Provider Section.\n"
            "Please follow `https://docs.opta.dev/getting-started/` to get started."
        )

    """
    Validates Configuration and throws Exception when proviers is provided but left Empty.
    name: Test Name
    org_name: Test Org Name
    providers:
        aws/google/azurerm:
    modules:...
    """
    if (
        ("aws" in providers and providers.get("aws") is None)
        or ("google" in providers and providers.get("google") is None)
        or ("azurerm" in providers and providers.get("azurerm") is None)
    ):
        raise UserErrors("Please provide the Details of Cloud Provider Used.")
