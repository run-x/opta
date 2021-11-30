from typing import TYPE_CHECKING

from modules.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsSnsProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-sns":
            raise Exception(
                f"The module {module.name} was expected to be of type aws sns"
            )
        super(AwsSnsProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        super(AwsSnsProcessor, self).process(module_idx)
