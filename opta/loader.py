# new-module-api
"""
Contains classes for loading objects from files
"""

from __future__ import annotations

import os
from typing import List, Optional

from opta.exceptions import UserErrors
from opta.layer2 import Layer
from opta.module_spec import SPEC_NAME, ModuleSpec
from opta.utils import yaml


class LayerLoader:
    def from_path(self, path: str) -> Layer:
        try:
            with open(path) as f:
                data = yaml.load(f)
        except FileNotFoundError:
            raise UserErrors(f"File {path} not found")

        return self.from_dict(data)

    def from_dict(self, raw: dict) -> Layer:
        layer = Layer.from_dict(raw)

        return layer


class ModuleSpecLoader:
    def load(self, module_path: str) -> ModuleSpec:
        spec_path = os.path.join(module_path, SPEC_NAME)
        with open(spec_path, "r") as f:
            spec_raw = yaml.load(f)

        return ModuleSpec.from_dict(module_path, spec_raw)

    def load_all(self, base_path: Optional[str] = None) -> List["ModuleSpec"]:
        if not base_path:
            base_path = os.path.join(os.path.dirname(__file__), "..", "modules")

        modules: List["ModuleSpec"] = []
        for child in os.scandir(base_path):
            if not self._is_module(child):
                continue

            modules.append(self.load(child.path))

        return modules

    def _is_module(self, dir: os.DirEntry[str]) -> bool:
        if not dir.is_dir():
            return False

        spec_path = os.path.join(dir.path, SPEC_NAME)
        return os.path.isfile(spec_path)
