from typing import TYPE_CHECKING

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpGkeProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GcpGkeProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        gcp_base_module = None
        for module in self.layer.modules:
            if module.data["type"] == "gcp-base":
                gcp_base_module = module
                break
        if gcp_base_module is None:
            raise UserErrors(
                "The gcp-gke module needs to be run on the same yaml as the gcp-base"
            )
        self.module.data[
            "vpc_self_link"
        ] = f"${{{{module.{gcp_base_module.name}.vpc_self_link}}}}"
        self.module.data[
            "private_subnet_self_link"
        ] = f"${{{{module.{gcp_base_module.name}.private_subnet_self_link}}}}"
        super(GcpGkeProcessor, self).process(module_idx)
