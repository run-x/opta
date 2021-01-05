import os
from typing import Any, Dict, Iterable

import yaml

from opta.plugins.derived_providers import DerivedProviders
from opta.utils import deep_merge, hydrate

REGISTRY = yaml.load(
    open(f"{os.path.dirname(__file__)}/../registry.yaml"), Loader=yaml.Loader
)
BACKEND_ENABLED = "enable-backend"
BACKEND_DISABLED = "disable-backend"
WAIT = "wait"


class BaseModule:
    def __init__(
        self,
        meta: Dict[Any, Any],
        key: str,
        data: Dict[Any, Any],
        layer: Any = None,
    ):
        self.meta = meta
        self.key = key
        self.desc = REGISTRY["modules"][data["type"]]
        self.name = f"{self.meta['name']}-{self.key}"
        self.layer = layer
        self.data = data

    def gen_blocks(self) -> Dict[Any, Any]:
        module_blk = {"module": {self.key: {"source": self.desc["location"]}}}
        for k, v in self.desc["variables"].items():
            if k in self.data:
                module_blk["module"][self.key][k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "name":
                module_blk["module"][self.key][k] = self.name
            elif self.layer is not None and k in self.layer.outputs():
                module_blk["module"][self.key][
                    k
                ] = f"${{data.terraform_remote_state.parent.outputs.{k}}}"
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


class Layer:
    def __init__(
        self,
        meta: Dict[Any, Any],
        data: Dict[Any, Any],
        child_meta: Dict[Any, Any] = {},
    ):
        self.meta = meta
        self.child_meta = child_meta
        self.modules = []

        for module_data in data["modules"]:
            if type(module_data) is dict:
                self.modules.append(
                    Module(
                        meta, list(module_data.keys())[0], list(module_data.values())[0]
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

    def gen_blocks(self) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        for m in self.modules:
            ret = deep_merge(m.gen_blocks(), ret)

        return ret

    def for_child(self) -> bool:
        return "parent" in self.child_meta

    def gen_providers(self, backend_enabled: bool) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {"provider": {}}

        for k, v in self.meta["providers"].items():
            ret["provider"][k] = v
            if k in REGISTRY["backends"]:
                hydration = {
                    "parent_name": self.meta["name"],
                    "child_name": self.child_meta["name"]
                    if "name" in self.child_meta
                    else "parent",
                }

                # Add the backend
                if backend_enabled:
                    ret["terraform"] = hydrate(
                        REGISTRY["backends"][k]["terraform"], hydration
                    )

                if self.for_child():
                    # Add remote state
                    backend, config = list(
                        REGISTRY["backends"][k]["terraform"]["backend"].items()
                    )[0]
                    ret["data"] = {
                        "terraform_remote_state": {
                            "parent": {
                                "backend": backend,
                                "config": hydrate(
                                    config,
                                    {
                                        "parent_name": self.meta["name"],
                                        "child_name": "parent",
                                    },
                                ),
                            }
                        }
                    }

                    # Add derived providers like k8s

                    ret = deep_merge(ret, DerivedProviders(self).gen_blocks())

        return ret


class Module(BaseModule):
    pass
