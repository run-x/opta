from typing import Any, Dict

from opta.utils import deep_merge


class DerivedProviders:
    def __init__(self, layer: Any):
        self.layer = layer

    def gen_tf(self) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        if self.layer is None:
            return ret
        for b in self.layer.blocks:
            for m in b.modules:
                if "providers" in m.desc:
                    ret = deep_merge(m.desc["providers"], ret)
        return ret
