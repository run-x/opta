from typing import TYPE_CHECKING, List

import boto3
from botocore.config import Config

from opta.exceptions import UserErrors
from opta.module_processors.base import GcpK8sModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpK8sServiceProcessor(GcpK8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "gcp-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        self.read_buckets: list[str] = []
        self.write_buckets: list[str] = []
        providers = layer.gen_providers(0)
        region = providers["terraform"]["backend"]["s3"]["region"]
        self.eks = boto3.client("eks", config=Config(region_name=region))
        super(GcpK8sServiceProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        transformed_secrets = []
        if "original_secrets" in self.module.data:
            secrets = self.module.data["original_secrets"]
        else:
            secrets = self.module.data.get("secrets", [])
            self.module.data["original_secrets"] = secrets
        for secret in secrets:
            if type(secret) is str:
                transformed_secrets.append({"name": secret, "value": ""})
            else:
                raise Exception("Secret must be string or dict")
        self.module.data["secrets"] = transformed_secrets

        # Handle links
        for link_data in self.module.data.get("links", []):
            if type(link_data) is str:
                target_module_name = link_data
                link_permissions = []
            elif type(link_data) is dict:
                target_module_name = list(link_data.keys())[0]
                link_permissions = list(link_data.values())[0]
            else:
                raise UserErrors(
                    f"Link data {link_data} must be a string or map holding the permissions"
                )
            module = self.layer.get_module(target_module_name, module_idx)
            if module is None:
                raise Exception(
                    f"Did not find the desired module {target_module_name} "
                    "make sure that the module you're referencing is listed before the k8s "
                    "app one"
                )
            module_type = module.data["type"]
            if module_type == "gcp-postgres":
                self.handle_rds_link(module, link_permissions)
            elif module_type == "gcp-redis":
                self.handle_redis_link(module, link_permissions)
            elif module_type == "gcp-gcs":
                self.handle_gcs_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )

        self.module.data["read_buckets"] = self.read_buckets
        self.module.data["write_buckets"] = self.write_buckets
        if "image_tag" in self.layer.variables:
            self.module.data["tag"] = self.layer.variables["image_tag"]
        super(GcpK8sServiceProcessor, self).process(module_idx)

    def handle_rds_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        pass

    def handle_redis_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        pass

    def handle_gcs_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        bucket_name = linked_module.data["bucket_name"]
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(bucket_name)
            elif permission == "write":
                self.write_buckets.append(bucket_name)
            else:
                raise Exception(f"Invalid permission {permission}")
