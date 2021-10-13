import os
from typing import TYPE_CHECKING

import click
from kubernetes.client import ApiException, CoreV1Api, V1Namespace, V1ObjectMeta, V1Secret
from kubernetes.config import load_kube_config
from requests import codes, get

from opta.core.kubernetes import configure_kubectl
from opta.core.terraform import get_terraform_outputs
from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import exp_backoff, logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AtlasMongoProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "atlas-mongo":
            raise Exception(
                f"The module {module.name} was expected to be of type atlas_mongo"
            )

        super(AtlasMongoProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        required_env_set = set(["MONGODB_ATLAS_PUBLIC_KEY", "MONGODB_ATLAS_PRIVATE_KEY",])

        if not required_env_set.issubset(set(os.environ.keys())):
            raise UserErrors(
                "Opta did not find environment variable(s), please set them and retry: {}".format(
                    required_env_set - set(os.environ.keys())
                )
            )

        super(AtlasMongoProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:

        self.module.data["cloud_provider"] = self.layer.cloud.upper()
        if self.module.data["cloud_provider"] == "LOCAL":
            self.module.data["cloud_provider"] = "AWS"  # For local, always spin up in AWS
            self.module.data["region"] = "US_EAST_1"
        base_layer = self.layer.root()
        root_outputs = get_terraform_outputs(base_layer)
        self.module.data["public_nat_ips"] =root_outputs["public_nat_ips"]

        super(AtlasMongoProcessor, self).process(module_idx)
