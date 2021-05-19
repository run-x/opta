from typing import TYPE_CHECKING

from opta.module_processors.base import ModuleProcessor, get_aws_base_module_refs

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
        aws_base_module_refs = get_aws_base_module_refs(self.layer)
        self.module.data["kms_key_id"] = aws_base_module_refs["kms_account_key_id"]
        super(AwsSnsProcessor, self).process(module_idx)
