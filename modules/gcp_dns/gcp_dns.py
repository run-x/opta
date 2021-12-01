from typing import TYPE_CHECKING

from modules.base import DNSModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GCPDnsProcessor(DNSModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if layer.parent is not None:
            raise UserErrors("GCP dns must be set on environment, not service")
        super(GCPDnsProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.validate_dns()
        super(GCPDnsProcessor, self).process(module_idx)
