from typing import TYPE_CHECKING

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsDocumentDbProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-documentdb":
            raise Exception(
                f"The module {module.name} was expected to be of type aws sns"
            )
        super(AwsDocumentDbProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        if self.module.data.__contains__("instance_count"):
            self.module.data["instance_count"] = self.module.data.get("instance_count")
        super(AwsDocumentDbProcessor, self).process(module_idx)
