import os
from typing import TYPE_CHECKING

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class CustomTerraformProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(CustomTerraformProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        current_desc = self.module.desc
        self.module.module_dir_path = os.path.join(
            os.path.dirname(self.layer.path), self.module.data["path_to_module"]
        )
        current_desc["variables"] = {
            x: "optional" for x in self.module.data.get("terraform_inputs", {}).keys()
        }
        self.module.data.update(self.module.data.get("terraform_inputs", {}))
