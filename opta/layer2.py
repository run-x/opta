# new-module-api

from __future__ import annotations

from typing import List, Optional

from opta.module2 import Module
from opta.stubs import Environment, ProviderConfig, from_dict


class Layer:
    name: str
    org_name: Optional[str]
    modules: List[Module]
    providers: ProviderConfig
    environments: List[Environment]

    def __init__(self, name: str) -> None:
        self.name = name
        self.org_name = None
        self.modules = []
        self.providers = ProviderConfig()
        self.environments = []

    def __repr__(self) -> str:
        return f"Layer(name={repr(self.name)}, modules={repr(self.modules)})"

    @classmethod
    def from_dict(cls, raw: dict) -> Layer:
        layer = cls(raw["name"])
        layer.org_name = raw.get("org_name")

        layer.modules = from_dict(Module, raw, "modules")
        layer.environments = from_dict(Environment, raw, "environments")
        layer.providers = ProviderConfig.from_dict(raw.get("providers", {}))

        return layer


Layer2 = Layer
