import os
from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class CustomTerraformProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(CustomTerraformProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        current_desc = self.module.desc
        path_to_module: str = self.module.data["path_to_module"]
        path_to_layer: str = os.path.abspath(os.path.dirname(self.layer.path))
        module_version: str = self.module.data.get("version", None) or ""
        if path_to_module.startswith("./"):
            path_to_module = path_to_module.strip("./")
            self.module.module_dir_path = os.path.join(path_to_layer, path_to_module)
        elif path_to_module.startswith("../"):
            self.module.module_dir_path = os.path.join(path_to_layer, path_to_module)
        else:
            # If this is the case, then this refers to a remote module as per
            # https://www.terraform.io/language/modules/sources
            self.module.module_dir_path = path_to_module
            if module_version == "":
                raise UserErrors(
                    "module_version must be given to custom terraform for non-local modules"
                )
        current_desc["inputs"] = [
            {"name": x, "user_facing": True}
            for x in self.module.data.get("terraform_inputs", {}).keys()
        ]
        if module_version != "":
            current_desc["inputs"].append({"name": "version", "user_facing": True})
        self.module.data.update(self.module.data.get("terraform_inputs", {}))
