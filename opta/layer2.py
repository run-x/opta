# new-module-api

from __future__ import annotations

import re
from typing import List, Optional, Set

from opta.constants import MODULE_DEPENDENCY
from opta.exceptions import UserErrors
from opta.module2 import Module
from opta.stubs import Environment, ProviderConfig, from_dict


class Layer:
    name: str
    org_name: Optional[str]
    parent: Optional[Layer]
    modules: List[Module]
    providers: ProviderConfig
    environments: List[Environment]

    def __init__(self, name: str, parent: Optional[Layer] = None) -> None:
        self.name = name
        self.org_name = None
        self.parent = parent
        self.modules = []
        self.providers = ProviderConfig()
        self.environments = []
        pattern = "^[A-Za-z0-9-]*$"
        if not bool(re.match(pattern, self.name)):
            raise UserErrors(
                "Invalid layer, can only contain letters, dashes and numbers!"
            )

    def __repr__(self) -> str:
        return f"Layer(name={repr(self.name)}, modules={repr(self.modules)})"

    @classmethod
    def from_dict(cls, raw: dict) -> Layer:
        layer = cls(raw["name"])
        layer.org_name = raw.get("org_name")

        layer.modules = from_dict(Module, raw, "modules")
        layer.environments = from_dict(Environment, raw, "environments")
        layer.providers = ProviderConfig.from_dict(raw.get("providers", {}))
        if layer.parent is None and layer.org_name is None:
            raise UserErrors("Config must have org name or a parent who has an org name")
        return layer

    @classmethod
    def validate_layer(cls, layer: "Layer") -> None:
        # Check for Uniqueness of Modules
        unique_modules: Set[str] = set()
        for module in layer.modules:
            if module.desc.get("is_unique", False) and unique_modules.__contains__(
                module.type
            ):
                raise UserErrors(
                    f"Module Type: '{module.type}' used twice in the configuration. Please check and update as required."
                )
            unique_modules.add(module.type)

        # Checks the Dependency Graph for Unresolved Dependencies.
        previous_modules: Set[str] = set()
        for module in layer.modules:
            dependency_modules = MODULE_DEPENDENCY.get(
                module.aliased_type or module.type, set()
            )
            for dependency_module in dependency_modules:
                if not previous_modules.__contains__(dependency_module):
                    raise UserErrors(
                        f'Module: "{module.type}" has it\'s dependency on a missing Module: "{dependency_module}". '
                        f"Please rectify the configuration before using it."
                    )
            previous_modules.add(module.aliased_type or module.type)


Layer2 = Layer
