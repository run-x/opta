import os
from typing import Any, Iterable, List, Mapping

import yaml
from plugins.derived_providers import DerivedProviders

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

    def gen_blocks(self) -> Iterable[Mapping[Any, Any]]:
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
            elif self.env is not None and k in self.env.outputs():
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
    def __init__(self, meta: Mapping[Any, Any], data: Mapping[Any, Any]):
        self.meta = meta
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

    def gen_blocks(self) -> Iterable[Mapping[Any, Any]]:
        ret: List[Mapping[Any, Any]] = []
        for m in self.modules:
            ret.extend(m.gen_blocks())

        return ret

    def gen_providers(self, include_derived: bool = False) -> Iterable[Mapping[Any, Any]]:
        ret = []

        for k, v in self.meta["providers"].items():
            blk = {"type": "provider", "key": k}
            blk.update(v)
            ret.append(blk)

        if include_derived:
            ret.extend(DerivedProviders(self, MODULES_DIR).gen_blocks())

        return ret


class Module(BaseModule):
    pass
