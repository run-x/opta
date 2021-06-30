from typing import TYPE_CHECKING, Dict, List, Union

from opta.core.kubernetes import create_namespace_if_not_exists, get_manual_secrets
from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureK8sServiceProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "azure-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s service"
            )
        self.read_buckets: list[str] = []
        self.write_buckets: list[str] = []
        super(AzureK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        create_namespace_if_not_exists(self.layer.name)
        manual_secrets = get_manual_secrets(self.layer.name)
        for secret_name in self.module.data.get("secrets", []):
            if secret_name not in manual_secrets:
                raise UserErrors(
                    f"Secret {secret_name} has not been set via opta secret update! Please do so before applying the "
                    f"K8s service w/ a new secret."
                )
        super(AzureK8sServiceProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["manual_secrets"] = self.module.data.get("secrets", [])
        self.module.data["link_secrets"] = self.module.data.get("link_secrets", [])

        if isinstance(self.module.data.get("public_uri"), str):
            self.module.data["public_uri"] = [self.module.data["public_uri"]]

        current_envars: Union[List, Dict[str, str]] = self.module.data.get("env_vars", [])
        if isinstance(current_envars, dict):
            self.module.data["env_vars"] = [
                {"name": x, "value": y} for x, y in current_envars.items()
            ]

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

        super(AzureK8sServiceProcessor, self).process(module_idx)
