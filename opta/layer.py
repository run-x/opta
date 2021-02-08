from __future__ import annotations

import os
import re
import shutil
import tempfile
from os import path
from typing import Any, Dict, Iterable, List, Optional

import git
import yaml

from opta.blocks import Blocks
from opta.constants import REGISTRY
from opta.plugins.derived_providers import DerivedProviders
from opta.plugins.link_processor import LinkProcessor
from opta.utils import deep_merge, hydrate


class Layer:
    def __init__(
        self,
        meta: Dict[Any, Any],
        blocks_data: List[Any],
        parent: Optional[Layer] = None,
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
    def load_from_yaml(cls, configfile: str, env: Optional[str]) -> Layer:
        if configfile.startswith("git@"):
            print("Loading layer from git...")
            git_url, file_path = configfile.split("//")
            branch = "main"
            if "?" in file_path:
                file_path, file_vars = file_path.split("?")
                res = dict(
                    map(
                        lambda x: (x.split("=")[0], x.split("=")[1]), file_vars.split(",")
                    )
                )
                branch = res.get("ref", branch)
            t = tempfile.mkdtemp()
            # Clone into temporary dir
            git.Repo.clone_from(git_url, t, branch=branch, depth=1)
            conf = yaml.load(open(os.path.join(t, file_path)), Loader=yaml.Loader)
            shutil.rmtree(t)
        elif path.exists(configfile):
            conf = yaml.load(open(configfile), Loader=yaml.Loader)
        else:
            raise Exception(f"File {configfile} not found")
        return cls.load_from_dict(conf, env)

    @classmethod
    def load_from_dict(cls, conf: Dict[Any, Any], env: Optional[str]) -> Layer:
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
        if "envs" in meta:
            envs = meta.pop("envs")
            if env is None:
                raise Exception(
                    "configfile has multiple environments, but you did not specify one"
                )
            potential_envs = []
            for env_meta in envs:
                current_parent = cls.load_from_yaml(env_meta["parent"], env)
                current_variables = env_meta.get("variables", {})
                potential_envs.append(current_parent.get_env())
                if current_parent.get_env() == env:
                    meta["parent"] = env_meta["parent"]
                    meta["variables"] = deep_merge(
                        meta.get("variables", {}), current_variables
                    )
                    return cls(meta, blocks_data, current_parent)
            raise Exception(f"Invalid env of {env}, valid ones are {potential_envs}")
        if "parent" in meta:
            parent = cls.load_from_yaml(meta["parent"], env)
        return cls(meta, blocks_data, parent)

    @staticmethod
    def valid_name(name: str) -> bool:
        pattern = "^[A-Za-z0-9-]*$"
        return bool(re.match(pattern, name))

    def get_env(self) -> str:
        if self.parent is not None:
            return self.parent.get_env()
        return self.meta["name"]

    def outputs(self, block_idx: Optional[int] = None) -> Iterable[str]:
        ret: List[str] = []
        block_idx = block_idx or len(self.blocks) - 1
        for block in self.blocks[0 : block_idx + 1]:
            ret += block.outputs()
        return ret

    def gen_tf(self, block_idx: int) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        current_modules = []
        for block in self.blocks[0 : block_idx + 1]:
            current_modules += block.modules
        LinkProcessor().process(current_modules)
        for block in self.blocks[0 : block_idx + 1]:
            ret = deep_merge(block.gen_tf(), ret)

        return hydrate(ret, self.metadata_hydration())

    def metadata_hydration(self) -> Dict[Any, Any]:
        parent_name = self.parent.meta["name"] if self.parent is not None else "nil"
        parent = (
            self.parent.meta.get("variables", {}) if self.parent is not None else "nil"
        )
        return deep_merge(
            self.meta.get("variables", {}),
            {
                "parent": parent,
                "parent_name": parent_name,
                "layer_name": self.meta["name"],
                "state_storage": self.state_storage(),
                "env": self.get_env(),
            },
        )

    def state_storage(self) -> str:
        if "state_storage" in self.meta:
            return self.meta["state_storage"]
        elif self.parent is not None:
            return self.parent.state_storage()
        return f"opta-tf-state-{self.meta['name']}"

    def gen_providers(self, block_idx: int, backend_enabled: bool) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {"provider": {}}
        providers = self.meta.get("providers", {})
        if self.parent is not None:
            providers = deep_merge(providers, self.parent.meta.get("providers", {}))
        for k, v in providers.items():
            ret["provider"][k] = v
            if k in REGISTRY["backends"]:
                if backend_enabled:
                    hydration = deep_merge(self.metadata_hydration(), {"provider": v})
                    ret["terraform"] = hydrate(
                        REGISTRY["backends"][k]["terraform"], hydration
                    )

                if self.parent is not None:
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
                                        "state_storage": self.state_storage(),
                                        "provider": self.parent.meta.get(
                                            "providers", {}
                                        ).get(k, {}),
                                    },
                                ),
                            }
                        }
                    }

        # Add derived providers like k8s from parent
        ret = deep_merge(ret, DerivedProviders(self.parent, is_parent=True).gen_tf())
        # Add derived providers like k8s from own blocks
        ret = deep_merge(
            ret, DerivedProviders(self, is_parent=False).gen_tf(block_idx=block_idx)
        )

        return ret
