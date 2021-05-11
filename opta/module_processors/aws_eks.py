from typing import TYPE_CHECKING

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsEksProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "aws-eks":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(AwsEksProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        if len(aws_base_modules) == 0:
            raise UserErrors(
                "Could not find aws base module in this opta yaml-- you need to have it for eks to work"
            )
        aws_base_module = aws_base_modules[0]
        self.module.data[
            "private_subnet_ids"
        ] = f"${{{{module.{aws_base_module.name}.private_subnet_ids}}}}"
        self.module.data[
            "kms_account_key_arn"
        ] = f"${{{{module.{aws_base_module.name}.kms_account_key_arn}}}}"
        super(AwsEksProcessor, self).process(module_idx)
