import json
import os
from typing import Any, Mapping

from utils import deep_merge


class DerivedProviders:
    def __init__(self, env: Any, modules_dir: str):
        self.env = env
        self.modules_dir = modules_dir

    def gen_blocks(self) -> Mapping[Any, Any]:
        ret: Mapping[Any, Any] = {}
        for m in self.env.modules:
            providers_file = f"{self.modules_dir}/{m.data['type']}/providers.json"
            if os.path.exists(providers_file):
                data = json.loads(open(providers_file).read())
                ret = deep_merge(data, ret)

        return ret
