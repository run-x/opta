from typing import TYPE_CHECKING

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsS3Processor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-s3":
            raise Exception(
                f"The module {module.name} was expected to be of type aws sns"
            )
        super(AwsS3Processor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        if len(aws_base_modules) == 0 and self.layer.parent is not None:
            from_parent = True
            aws_base_modules = self.layer.parent.get_module_by_type("aws-base")

        if len(aws_base_modules) == 0:
            raise UserErrors(
                "Did not find the aws-eks module in the layer or the parent layer"
            )

        module_source = (
            "data.terraform_remote_state.parent.outputs"
            if from_parent
            else f"module.{aws_base_modules[0].name}"
        )
        self.module.data["s3_log_bucket_name"] = self.module.data.get(
            "s3_log_bucket_name", f"${{{{{module_source}.s3_log_bucket_name}}}}"
        )
        super(AwsS3Processor, self).process(module_idx)
