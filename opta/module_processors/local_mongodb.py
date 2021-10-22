from typing import TYPE_CHECKING, Dict

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class LocalMongoDBProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(LocalMongoDBProcessor, self).__init__(module, layer)

    def get_event_properties(self) -> Dict[str, int]:
        return {"module_local_mongodb": 1}
