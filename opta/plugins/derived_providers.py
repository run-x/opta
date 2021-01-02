from typing import Any, Mapping

from utils import deep_merge


class DerivedProviders:
    def __init__(self, env: Any):
        self.env = env

    def gen_blocks(self) -> Mapping[Any, Any]:
        ret: Mapping[Any, Any] = {}
        for m in self.env.modules:
            if "providers" in m.desc:
                ret = deep_merge(m.desc["providers"], ret)

        return ret
