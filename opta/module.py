import os
from typing import Any, Iterable, Mapping

import yaml
from plugins.derived_providers import DerivedProviders
from utils import deep_merge

MODULES_DIR = os.environ.get("OPTA_MODULES_DIR")


class BaseModule:
    def __init__(
        self, meta: Mapping[Any, Any], key: str, data: Mapping[Any, Any], env: Any = None,
    ):
        self.meta = meta
        self.key = key
        self.desc = yaml.load(
            open(f"{MODULES_DIR}/{data['type']}/module.yaml"), Loader=yaml.Loader
        )
        self.name = f"{self.meta['name']}-{self.key}"
        self.env = env
        self.data = data

    def gen_blocks(self) -> Mapping[Any, Any]:
        module_blk = {
            "module": {self.key: {"source": f"{MODULES_DIR}/{self.data['type']}"}}
        }
        for k, v in self.desc["variables"].items():
            if k in self.data:
                module_blk["module"][self.key][k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "name":
                module_blk["module"][self.key][k] = self.name
            elif self.env is not None and k in self.env.outputs():
                module_blk["module"][self.key][
                    k
                ] = f"${{data.terraform_remote_state.env.outputs.{k}}}"
            else:
                raise Exception(f"Unable to hydrate {k}")

        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if v == "export":
                    if "output" not in module_blk:
                        module_blk["output"] = {}

                    module_blk["output"].update({k: {"value": f"module.{self.key}.{k}"}})

        return module_blk


class Env:
    def __init__(self, meta: Mapping[Any, Any], data: Mapping[Any, Any], path: str = "."):
        self.meta = meta
        self.path = path
        self.modules = []

        for k, v in data.items():
            self.modules.append(Module(meta, k, v))

    def outputs(self) -> Iterable[str]:
        ret = []

        for m in self.modules:
            if "outputs" in m.desc:
                for k, v in m.desc["outputs"].items():
                    if v == "export":
                        ret.append(k)

        return ret

    def gen_blocks(self) -> Mapping[Any, Any]:
        ret: Mapping[Any, Any] = {}
        for m in self.modules:
            ret = deep_merge(m.gen_blocks(), ret)

        return ret

    def gen_providers(self, include_derived: bool = False) -> Mapping[Any, Any]:
        ret: Mapping[Any, Any] = {"provider": {}}

        for k, v in self.meta["providers"].items():
            ret["provider"][k] = v

        if include_derived:
            ret = deep_merge(ret, DerivedProviders(self, MODULES_DIR).gen_blocks())

        return ret

    def gen_remote_state(self) -> Mapping[Any, Any]:
        state_path = "." if "/" not in self.path else os.path.dirname(self.path)
        return {
            "data": {
                "terraform_remote_state": {
                    "env": {
                        "backend": "local",
                        "config": {"path": f"{state_path}/terraform.tfstate"},
                    }
                }
            }
        }


class Module(BaseModule):
    pass
