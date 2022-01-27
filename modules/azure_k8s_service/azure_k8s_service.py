from typing import TYPE_CHECKING, Any, Dict, List, Union

from modules.base import K8sServiceModuleProcessor
from opta.core.kubernetes import create_namespace_if_not_exists
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureK8sServiceProcessor(K8sServiceModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "azure-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        super(AzureK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        create_namespace_if_not_exists(self.layer.name)
        super(AzureK8sServiceProcessor, self).pre_hook(module_idx)

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
            if module_type == "azure-postgres":
                self.handle_rds_link(module, link_permissions)
            elif module_type == "azure-redis":
                self.handle_redis_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )

        acr_module_source: str
        if self.layer.parent is None:
            base_modules = self.layer.get_module_by_type("azure-base")
            if len(base_modules) == 0:
                raise UserErrors("Could not find base module for azure")
            acr_module_source = f"module.{base_modules[0].name}"
        else:
            acr_module_source = "data.terraform_remote_state.parent.outputs"

        self.module.data["acr_registry_name"] = f"${{{{{acr_module_source}.acr_name}}}}"
        if "image_tag" in self.layer.variables:
            self.module.data["tag"] = self.layer.variables["image_tag"]

        if "image_digest" in self.layer.variables:
            self.module.data["digest"] = self.layer.variables["image_digest"]

        super(AzureK8sServiceProcessor, self).process(module_idx)

    # TODO: consolidated repeated credential link code
    def handle_rds_link(
        self, linked_module: "Module", link_permissions: List[Any]
    ) -> None:
        required_db_vars = ["db_user", "db_name", "db_password", "db_host"]
        renamed_vars = {}
        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_db_vars
            ):
                raise UserErrors(
                    f"To rename db variables you must provide aliases for these fields: {required_db_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("DB variable rename must be only to another string")

        for key in required_db_vars:
            self.module.data["link_secrets"].append(
                {
                    "name": renamed_vars.get(key, f"{linked_module.name}_{key}"),
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
        self, linked_module: "Module", link_permissions: List[Any]
    ) -> None:
        required_redis_vars = ["cache_host", "cache_auth_token"]
        renamed_vars = {}

        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_redis_vars
            ):
                raise UserErrors(
                    f"To rename redis variables you must provide aliases for these fields: {required_redis_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("Redis variable rename must be only to another string")

        for key in required_redis_vars:
            self.module.data["link_secrets"].append(
                {
                    "name": renamed_vars.get(key, f"{linked_module.name}_{key}"),
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
