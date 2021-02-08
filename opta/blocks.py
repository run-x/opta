from typing import Any, Dict, Iterable

from opta.module import Module
from opta.utils import deep_merge


class Blocks:
    def __init__(
        self,
        layer_name: str,
        module_data: Dict[Any, Any],
        backend_enabled: bool = True,
        parent_layer: Any = None,
    ):
        self.backend_enabled = backend_enabled
        self.modules = []
        self.parent_layer = parent_layer
        for module_key, module_data in module_data.items():
            self.modules.append(
                Module(
                    layer_name,
                    module_key,
                    module_data,
                    self.parent_layer,
                )
            )

    def outputs(self) -> Iterable[str]:
        ret = []
        for m in self.modules:
            if "outputs" in m.desc:
                for k, v in m.desc["outputs"].items():
                    if "export" in v and v["export"]:
                        ret.append(k)

        return ret

    def gen_tf(self) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        for m in self.modules:
            ret = deep_merge(m.gen_tf(), ret)

        return ret
