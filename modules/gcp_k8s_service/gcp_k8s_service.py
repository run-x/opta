from typing import TYPE_CHECKING, Dict, List, Union

from modules.base import GcpK8sModuleProcessor, K8sServiceModuleProcessor
from modules.linker_helper import LinkerHelper
from opta.core.kubernetes import create_namespace_if_not_exists
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpK8sServiceProcessor(GcpK8sModuleProcessor, K8sServiceModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "gcp-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        super(GcpK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        create_namespace_if_not_exists(self.layer.name)
        super(GcpK8sServiceProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["link_secrets"] = self.module.data.get("link_secrets", [])

        current_envars: Union[List, Dict[str, str]] = self.module.data.get("env_vars", [])
        if isinstance(current_envars, dict):
            self.module.data["env_vars"] = [
                {"name": x, "value": y} for x, y in current_envars.items()
            ]

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
            if module_type == "gcp-postgres" or module_type == "gcp-mysql":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "gcp-redis":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["cache_host", "cache_auth_token"],
                )
            elif module_type == "gcp-gcs":
                self.handle_gcs_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )

        self.module.data["read_buckets"] = (
            self.module.data.get("read_buckets", []) + self.read_buckets
        )
        self.module.data["write_buckets"] = (
            self.module.data.get("write_buckets", []) + self.write_buckets
        )
        if "image_tag" in self.layer.variables:
            self.module.data["tag"] = self.layer.variables["image_tag"]

        if "image_digest" in self.layer.variables:
            self.module.data["digest"] = self.layer.variables["image_digest"]
        seen = set()
        self.module.data["link_secrets"] = [
            seen.add(obj["name"]) or obj  # type: ignore
            for obj in self.module.data["link_secrets"]
            if obj["name"] not in seen
        ]
        super(GcpK8sServiceProcessor, self).process(module_idx)

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
