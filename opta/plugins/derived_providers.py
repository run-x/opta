import json
import os
from typing import Any, Iterable, Mapping


class DerivedProviders:
    def __init__(self, env: Any, modules_dir: str):
        self.env = env
        self.modules_dir = modules_dir

    def gen_blocks(self) -> Iterable[Mapping[Any, Any]]:
        ret = []
        for m in self.env.modules:
            providers_file = f"{self.modules_dir}/{m.data['type']}/providers.json"
            if os.path.exists(providers_file):
                data = json.loads(open(providers_file).read())
                ret.extend(data["items"])

        return ret
