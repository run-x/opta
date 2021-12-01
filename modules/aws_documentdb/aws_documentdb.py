from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsDocumentDbProcessor(ModuleProcessor):
    MIN_ALLOWED = 1  # AWS defined minimum
    MAX_ALLOWED = 16  # AWS defined maximum

    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-documentdb":
            raise Exception(
                f"The module {module.name} was expected to be of type aws sns"
            )
        super(AwsDocumentDbProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        if self.module.data.__contains__("instance_count"):
            instance_count: int = self.module.data.get("instance_count")  # type: ignore
            if self.MIN_ALLOWED > instance_count or self.MAX_ALLOWED < instance_count:
                raise UserErrors(
                    f"AWS allows Document DB Instaces only between {self.MIN_ALLOWED} and {self.MAX_ALLOWED}"
                )
            self.module.data["instance_count"] = self.module.data.get("instance_count")
        super(AwsDocumentDbProcessor, self).process(module_idx)
