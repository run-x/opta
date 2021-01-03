from typing import Any, Dict

from opta.utils import deep_merge


class DerivedProviders:
    def __init__(self, env: Any):
        self.env = env

    def gen_blocks(self) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        for m in self.env.modules:
            if "providers" in m.desc:
                ret = deep_merge(m.desc["providers"], ret)

        return ret
