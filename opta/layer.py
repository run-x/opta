import re
import yaml
from os import path
from typing import Any, Dict, Iterable, List

from opta.plugins.derived_providers import DerivedProviders
from opta.constants import REGISTRY
from opta.utils import deep_merge, hydrate
from opta.plugins.link_processor import LinkProcessor
from opta.blocks import Blocks


class Layer:
    def __init__(
        self,
        meta: Dict[Any, Any],
        blocks_data: List[Any],
        parent: Any = None,
    ):
        self.meta = meta
        self.parent = parent
        if not Layer.valid_name(self.meta["name"]):
            raise Exception(
                "Invalid layer, can only contain lowercase letters, numbers and hyphens!"
            )
        self.blocks = []
        for block_data in blocks_data:
            self.blocks.append(
                Blocks(
                    self.meta["name"],
                    block_data["modules"],
                    block_data.get("backend", "enabled") == "enabled",
                    self.parent,
                )
            )

    @classmethod
    def load_from_yaml(cls, configfile):
        if not path.exists(configfile):
            raise Exception(f"File {configfile} not found")
        conf = yaml.load(open(configfile), Loader=yaml.Loader)
        meta = conf.pop("meta")
        for macro_name, macro_value in REGISTRY["macros"].items():
            if macro_name in conf:
                conf.pop(macro_name)
                conf = deep_merge(conf, macro_value)
        blocks_data = conf.get("blocks", [])
        modules_data = conf.get("modules")
        if modules_data is not None:
            blocks_data.append({"modules": modules_data})
        parent = None
        if "parent" in meta:
            parent = cls.load_from_yaml(meta["parent"])
        return cls(meta, blocks_data, parent)

    @staticmethod
    def valid_name(name: str) -> bool:
        pattern = "^[A-Za-z0-9-]*$"
        return bool(re.match(pattern, name))

    def outputs(self, block_idx: int = None) -> Iterable[str]:
        ret = []
        block_idx = block_idx or len(self.blocks) - 1
        for block in self.blocks[0 : block_idx + 1]:
            ret += block.outputs()
        return ret

    def gen_tf(self, block_idx: int = None) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        block_idx = block_idx or len(self.blocks) - 1
        current_modules = []
        for block in self.blocks[0 : block_idx + 1]:
            current_modules += block.modules
        LinkProcessor().process(current_modules)
        for block in self.blocks[0:block_idx]:
            ret = deep_merge(block.gen_tf(), ret)
        hydration = {
            "parent_name": self.parent.meta["name"] if self.parent is not None else "nil",
            "layer_name": self.meta["name"],
            "state_storage": self.state_storage(),
        }

        return hydrate(ret, hydration)

    def for_child(self) -> bool:
        return self.parent is not None

    def state_storage(self) -> str:
        if "state_storage" in self.meta:
            return self.meta["state_storage"]
        elif self.parent is not None:
            return self.parent.state_storage()
        return f"opta-tf-state-{self.meta['name']}"

    def gen_providers(self, backend_enabled: bool) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {"provider": {}}
        providers = self.meta.get("providers", {})
        if self.parent is not None:
            providers = deep_merge(providers, self.parent.meta.get("providers", {}))
        for k, v in providers.items():
            ret["provider"][k] = v
            if k in REGISTRY["backends"]:
                hydration = {
                    "parent_name": self.parent.meta["name"]
                    if self.parent is not None
                    else "nil",
                    "layer_name": self.meta["name"],
                    "state_storage": self.state_storage(),
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
                                        "layer_name": self.parent.meta["name"],
                                    },
                                ),
                            }
                        }
                    }

                    # Add derived providers like k8s
                    ret = deep_merge(ret, DerivedProviders(self.parent).gen_tf())

        return ret
