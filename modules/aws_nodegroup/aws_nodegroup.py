from typing import TYPE_CHECKING

from modules.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsNodegroup(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super().__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.__back_compat_use_gpu()
        super(AwsNodegroup, self).process(module_idx)

    def __back_compat_use_gpu(self) -> None:
        if self.module.data.get("use_gpu", False):
            self.module.data["ami_type"] = "AL2_x86_64_GPU"
