from typing import TYPE_CHECKING, List

from opta.core.kubernetes import create_namespace_if_not_exists, get_manual_secrets
from opta.exceptions import UserErrors
from opta.module_processors.base import GcpK8sModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpK8sServiceProcessor(GcpK8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "gcp-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        self.read_buckets: list[str] = []
        self.write_buckets: list[str] = []
        super(GcpK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        create_namespace_if_not_exists(self.layer.name)
        manual_secrets = get_manual_secrets(self.layer.name)
        for secret_name in self.module.data.get("secrets", []):
            if secret_name not in manual_secrets:
                raise UserErrors(
                    f"Secret {secret_name} has not been set via opta secret update! Please do so before applying the "
                    f"K8s service w/ a new secret."
                )
        super(GcpK8sServiceProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["manual_secrets"] = self.module.data.get("secrets", [])
        self.module.data["link_secrets"] = self.module.data.get("link_secrets", [])

        if isinstance(self.module.data.get("public_uri"), str):
            self.module.data["public_uri"] = [self.module.data["public_uri"]]

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
            module_type = module.aliased_type or module.type
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
        seen = set()
        self.module.data["link_secrets"] = [
            seen.add(obj["name"]) or obj  # type: ignore
            for obj in self.module.data["link_secrets"]
            if obj["name"] not in seen
        ]
        super(GcpK8sServiceProcessor, self).process(module_idx)

    def handle_rds_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        for key in ["db_user", "db_name", "db_password", "db_host"]:
            self.module.data["link_secrets"].append(
                {
                    "name": f"{linked_module.name}_{key}",
                    "value": f"${{{{module.{linked_module.name}.{key}}}}}",
                }
            )
        if link_permissions:
            raise Exception(
                "We're not supporting IAM permissions for rds right now. "
                "Your k8s service will have the db user, name, password, "
                "and host as envars (pls see docs) and these IAM "
                "permissions are for manipulating the db itself, which "
                "I don't think is what you're looking for."
            )

    def handle_redis_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        for key in ["cache_host", "cache_auth_token"]:
            self.module.data["link_secrets"].append(
                {
                    "name": f"{linked_module.name}_{key}",
                    "value": f"${{{{module.{linked_module.name}.{key}}}}}",
                }
            )
        if link_permissions:
            raise Exception(
                "We're not supporting IAM permissions for redis right now. "
                "Your k8s service will have the cache's host and auth token "
                "as envars (pls see docs) and these IAM permissions "
                "are for manipulating the redis cluster itself, which "
                "I don't think is what you're looking for."
            )

    def handle_gcs_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(
                    f"${{{{module.{linked_module.name}.bucket_name}}}}"
                )
            elif permission == "write":
                self.write_buckets.append(
                    f"${{{{module.{linked_module.name}.bucket_name}}}}"
                )
            else:
                raise Exception(f"Invalid permission {permission}")
