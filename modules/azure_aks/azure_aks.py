from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.core.kubernetes import get_cluster_name, purge_opta_kube_config
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureAksProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AzureAksProcessor, self).__init__(module, layer)

    def post_delete(self, module_idx: int) -> None:
        purge_opta_kube_config(layer=self.layer)

    def process(self, module_idx: int) -> None:
        azure_base_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "azure-base":
                azure_base_module = module
                break
        if azure_base_module is None:
            raise UserErrors(
                "The azure-aks module needs to be run on the same yaml as the azure-base"
            )
        self.module.data["cluster_name"] = get_cluster_name(self.layer.root())
        self.module.data[
            "vpc_name"
        ] = f"${{{{module.{azure_base_module.name}.vpc_name}}}}"
        self.module.data[
            "private_subnet_name"
        ] = f"${{{{module.{azure_base_module.name}.private_subnet_name}}}}"
        super(AzureAksProcessor, self).process(module_idx)
