import os
from typing import Any, Dict, Iterable, Mapping

import yaml
from plugins.derived_providers import DerivedProviders
from utils import deep_merge, hydrate

REGISTRY = yaml.load(
    open(f"{os.path.dirname(__file__)}/../registry.yaml"), Loader=yaml.Loader
)


class BaseModule:
    def __init__(
        self, meta: Mapping[Any, Any], key: str, data: Mapping[Any, Any], env: Any = None,
    ):
        self.meta = meta
        self.key = key
        self.desc = REGISTRY["modules"][data["type"]]
        self.name = f"{self.meta['name']}-{self.key}"
        self.env = env
        self.data = data

    def gen_blocks(self) -> Mapping[Any, Any]:
        module_blk = {"module": {self.key: {"source": self.desc["location"]}}}
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
                if "export" in v and v["export"]:
                    if "output" not in module_blk:
                        module_blk["output"] = {}

                    module_blk["output"].update(
                        {k: {"value": f"${{module.{self.key}.{k}}}"}}
                    )

        return module_blk


class Env:
    def __init__(
        self,
        meta: Mapping[Any, Any],
        data: Mapping[Any, Any],
        child_meta: Mapping[Any, Any] = {},
    ):
        self.meta = meta
        self.child_meta = child_meta
        self.modules = []

        for k, v in data.items():
            self.modules.append(Module(meta, k, v))

    def outputs(self) -> Iterable[str]:
        ret = []

        for m in self.modules:
            if "outputs" in m.desc:
                for k, v in m.desc["outputs"].items():
                    if "export" in v and v["export"]:
                        ret.append(k)

        return ret

    def gen_blocks(self) -> Mapping[Any, Any]:
        ret: Mapping[Any, Any] = {}
        for m in self.modules:
            ret = deep_merge(m.gen_blocks(), ret)

        return ret

    def for_child(self) -> bool:
        return "env" in self.child_meta

    def gen_providers(self, init: bool) -> Mapping[Any, Any]:
        ret: Dict[Any, Any] = {"provider": {}}

        for k, v in self.meta["providers"].items():
            ret["provider"][k] = v
            if k in REGISTRY["backends"]:
                hydration = {
                    "env_name": self.meta["name"],
                    "child_name": self.child_meta["name"]
                    if "name" in self.child_meta
                    else "env",
                }

                # Add the backend
                if not init:
                    ret["terraform"] = hydrate(
                        REGISTRY["backends"][k]["terraform"], hydration
                    )

                if not self.for_child():
                    # Add the state bucket
                    ret["resource"] = hydrate(
                        REGISTRY["backends"][k]["resource"], hydration
                    )
                else:
                    # Add remote state
                    backend, config = list(
                        REGISTRY["backends"][k]["terraform"]["backend"].items()
                    )[0]
                    ret["data"] = {
                        "terraform_remote_state": {
                            "env": {
                                "backend": backend,
                                "config": hydrate(
                                    config,
                                    {"env_name": self.meta["name"], "child_name": "env"},
                                ),
                            }
                        }
                    }

                    # Add derived providers like k8s
                    ret = deep_merge(ret, DerivedProviders(self).gen_blocks())

        return ret


class Module(BaseModule):
    pass
