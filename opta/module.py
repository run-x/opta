import os
from typing import Any, Iterable, Mapping

import yaml

MODULES_DIR = os.environ.get("OPTA_MODULES_DIR")


class BaseModule:
    def __init__(
        self, meta: Mapping[Any, Any], key: str, data: Mapping[Any, Any], env: Any,
    ):
        self.meta = meta
        self.key = key
        self.desc = yaml.load(
            open(f"{MODULES_DIR}/{data['type']}/module.yaml"), Loader=yaml.Loader
        )
        self.name = f"{self.meta['name']}-{self.key}"
        self.env = env
        self.data = data

    def gen_blocks(self) -> Iterable[Mapping[Any, Any]]:
        print(self.data)
        print(self.desc)
        print(self.env.outputs)
        module_blk = {
            "type": "module",
            "key": self.key,
            "source": f"{MODULES_DIR}/{self.data['type']}",
        }
        for k, v in self.desc["variables"].items():
            if k in self.data:
                module_blk[k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "name":
                module_blk[k] = self.name
            elif k in self.env.outputs:
                module_blk[k] = f"${{data.terraform_remote_state.env.outputs.{k}}}"
            else:
                raise Exception(f"Unable to hydrate {k}")

        ret = [module_blk]
        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if v == "export":
                    ret.append(
                        {"type": "output", "key": k, "value": f"module.{self.key}.{k}"}
                    )

        return ret


class Env:
    def __init__(self, data: Mapping[Any, Any]):
        self.outputs = []

        for k, v in data.items():
            if k == "meta":
                continue

            desc = yaml.load(
                open(f"{MODULES_DIR}/{v['type']}/module.yaml"), Loader=yaml.Loader
            )
            if "outputs" in desc:
                self.outputs.extend(desc["outputs"])

    def gen_env_blocks(self) -> Iterable[Mapping[Any, Any]]:
        return []


class Module(BaseModule):
    pass
