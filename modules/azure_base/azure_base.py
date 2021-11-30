from typing import TYPE_CHECKING

from modules.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureBaseProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "azure-base":
            raise Exception(
                f"The module {module.name} was expected to be of type azure base"
            )
        super(AzureBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.module.data["location"] = self.layer.providers["azurerm"]["location"]
        super(AzureBaseProcessor, self).process(module_idx)
