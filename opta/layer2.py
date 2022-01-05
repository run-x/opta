from typing import List, Optional, Type

from opta.module2 import Module
from opta.stubs import Provider, Environment, from_dict


class Layer:
    name: str
    org_name: Optional[str]
    modules: List[Module]
    providers: List[Provider]
    environments: List[Environment]

    def __init__(self, name: str) -> None:
        self.name = name
        self.org_name = None
        self.modules = []
        self.providers = []
        self.environments = []

    def __repr__(self) -> str:
        return f"Layer(name={repr(self.name)}, modules={repr(self.modules)})"

    @classmethod
    def from_dict(cls, raw: dict) -> "Layer":
        layer = cls(raw["name"])
        layer.org_name = raw.get("org_name")

        layer.modules = from_dict(Module, raw, "modules")
        layer.providers = from_dict(Provider, raw, "provider")
        layer.environments = from_dict(Environment, raw, "environments")

        return layer

Layer2 = Layer
