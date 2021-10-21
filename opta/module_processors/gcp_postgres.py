from typing import TYPE_CHECKING, Dict

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GCPPostgresProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GCPPostgresProcessor, self).__init__(module, layer)

    def get_instance_count_keys(self) -> Dict[str, int]:
        return {"module_gcp_postgres": 1}
