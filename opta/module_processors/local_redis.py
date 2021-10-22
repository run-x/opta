from typing import TYPE_CHECKING, Dict

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class LocalRedisProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(LocalRedisProcessor, self).__init__(module, layer)

    def get_event_properties(self) -> Dict[str, int]:
        return {"module_local_redis": 1}
