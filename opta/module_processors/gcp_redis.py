from typing import TYPE_CHECKING, Dict

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GCPRedisProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GCPRedisProcessor, self).__init__(module, layer)

    def get_event_properties(self) -> Dict[str, int]:
        return {"module_gcp_redis": 1}
