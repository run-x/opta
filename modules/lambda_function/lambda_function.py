import os
from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class LambdaFunctionProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "lambda-function":
            raise Exception(
                f"The module {module.name} was expected to be of type lambda-function"
            )
        super(LambdaFunctionProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        base_from_parent = False
        if len(aws_base_modules) == 0 and self.layer.parent is not None:
            aws_base_modules = self.layer.parent.get_module_by_type("aws-base")
            base_from_parent = True

        if len(aws_base_modules) > 0:
            aws_base_module = aws_base_modules[0]
            module_source = (
                "data.terraform_remote_state.parent.outputs"
                if base_from_parent
                else f"module.{aws_base_module.name}"
            )
            self.module.data["vpc_id"] = f"${{{{{module_source}.vpc_id}}}}"
        file_path: str = self.module.data.get("filename")
        if not file_path.startswith("/"):
            file_path = os.path.join(os.path.dirname(self.layer.path), file_path)
        file_size = os.path.getsize(file_path) if file_path is not None else 0
        self.module.data["filename"] = file_path

        if file_size >= 50000000:
            raise UserErrors(
                "We're very sorry, but Opta currently only supports uploading zips of max 50 MB to lambda. "
                "Please raise this issue to the Opta maintainers so that we may expedite this feature enhancement"
            )
        super(LambdaFunctionProcessor, self).process(module_idx)
