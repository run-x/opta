from typing import TYPE_CHECKING, Dict, List, Union

from modules.base import K8sServiceModuleProcessor, LocalK8sModuleProcessor
from modules.linker_helper import LinkerHelper
from opta.core.kubernetes import create_namespace_if_not_exists, list_namespaces
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class LocalK8sServiceProcessor(LocalK8sModuleProcessor, K8sServiceModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "local-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type local k8s service"
            )
        super(LocalK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        list_namespaces()
        create_namespace_if_not_exists(self.layer.name)
        super(LocalK8sServiceProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["link_secrets"] = self.module.data.get("link_secrets", [])

        if isinstance(self.module.data.get("public_uri"), str):
            self.module.data["public_uri"] = [self.module.data["public_uri"]]

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
            if module_type == "local-postgres":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "local-redis":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["cache_host"],
                )
            elif module_type == "local-mongodb":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "local-mysql":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "mongodb-atlas":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=[
                        "db_password",
                        "db_user",
                        "mongodb_atlas_connection_string",
                    ],
                )
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
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
        super(LocalK8sServiceProcessor, self).process(module_idx)
