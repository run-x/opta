from typing import TYPE_CHECKING

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureK8sBaseProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "azure-k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(AzureK8sBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        azure_dns_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "azure-dns":
                azure_dns_module = module
                break
        if azure_dns_module is not None:
            self.module.data[
                "hosted_zone_name"
            ] = f"${{{{module.{azure_dns_module.name}.domain}}}}"
            self.module.data[
                "delegated"
            ] = f"${{{{module.{azure_dns_module.name}.delegated}}}}"
        super(AzureK8sBaseProcessor, self).process(module_idx)
