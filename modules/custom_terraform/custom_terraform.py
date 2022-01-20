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
        source: str = self.module.data.get("source") or self.module.data.get(
            "path_to_module"
        )
        if source is None:
            raise UserErrors("Need to specify source (formerly path_to_module)")
        path_to_layer: str = os.path.abspath(os.path.dirname(self.layer.path))
        module_version: str = self.module.data.get("version", None) or ""
        if source.startswith("./"):
            source = source.strip("./")
            self.module.module_dir_path = os.path.join(path_to_layer, source)
        elif source.startswith("../"):
            self.module.module_dir_path = os.path.join(path_to_layer, source)
        else:
            # If this is the case, then this refers to a remote module as per
            # https://www.terraform.io/language/modules/sources
            self.module.module_dir_path = source
        current_desc["inputs"] = [
            {"name": x, "user_facing": True}
            for x in self.module.data.get("terraform_inputs", {}).keys()
        ]
        if module_version != "":
            current_desc["inputs"].append({"name": "version", "user_facing": True})
        self.module.data.update(self.module.data.get("terraform_inputs", {}))
