from typing import TYPE_CHECKING, Dict

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class LocalMYSQLProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(LocalMYSQLProcessor, self).__init__(module, layer)

    def get_instance_count_keys(self) -> Dict[str, int]:
        return {"module_local_mysql": 1}
