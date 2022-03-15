# new-module-api

from __future__ import annotations

from typing import List, Optional

from opta.input_variable import InputVariable
from opta.module2 import Module
from opta.stubs import Environment, LayerProviderConfig
from opta.utils import multi_from_dict


class Layer:
    name: str
    org_name: Optional[str]
    modules: List[Module]
    providers: LayerProviderConfig
    environments: List[Environment]
    input_variables: List[InputVariable]

    def __init__(self, name: str) -> None:
        self.name = name
        self.org_name = None
        self.modules = []
        self.providers = LayerProviderConfig()
        self.environments = []
        self.input_variables = []

    def __repr__(self) -> str:
        return f"Layer(name={repr(self.name)}, modules={repr(self.modules)})"

    @classmethod
    def from_dict(cls, raw: dict) -> Layer:
        layer = cls(raw["name"])
        layer.org_name = raw.get("org_name")

        layer.modules = multi_from_dict(Module, raw, "modules")
        layer.input_variables = multi_from_dict(InputVariable, raw, "input_variables")
        layer.environments = multi_from_dict(Environment, raw, "environments")
        layer.providers = LayerProviderConfig.from_dict(raw.get("providers", {}))

        return layer


Layer2 = Layer
