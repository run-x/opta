# new-module-api

from __future__ import annotations

from typing import List, Optional
from opta.module2 import Module
from opta.stubs import Environment, ProviderConfig, from_dict
import re
from opta.exceptions import UserErrors
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
        if self.parent is None and self.org_name is None:
            raise UserErrors("Config must have org name or a parent who has an org name")

    def __repr__(self) -> str:
        return f"Layer(name={repr(self.name)}, modules={repr(self.modules)})"

    @classmethod
    def from_dict(cls, raw: dict) -> Layer:
        validate_layer_init(cls.name, cls.parent, cls.org_name)
        layer = cls(raw["name"])
        layer.org_name = raw.get("org_name")

        layer.modules = from_dict(Module, raw, "modules")
        layer.environments = from_dict(Environment, raw, "environments")
        layer.providers = ProviderConfig.from_dict(raw.get("providers", {}))

        return layer
    

Layer2 = Layer
