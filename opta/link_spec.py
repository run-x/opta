from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

from opta.utils import schema
from opta.utils.ref import Reference

T = TypeVar("T", bound="LinkSpec")


@dataclass  # TODO: In Python 3.10, pass in kw_only=True
class LinkConnectionSpec:
    source: Reference
    target: Reference

    @classmethod
    def from_dict(cls, raw: Dict[str, str]) -> "LinkConnectionSpec":
        if "both" in raw:
            if len(raw) > 1:
                raise ValueError("Unexpected `both` key in connection")

            source = raw["both"]
            target = raw["both"]
        else:
            source = raw["source"]
            target = raw["target"]

        c = cls(source=Reference.parse(source), target=Reference.parse(target),)

        return c

    @classmethod
    def from_dict_all(cls, raw_all: List[Dict[str, str]]) -> List["LinkConnectionSpec"]:
        return [cls.from_dict(raw) for raw in raw_all]


class LinkSpec:
    def __init__(self, type: str) -> None:
        self.type = type
        self._alias: Optional[str] = None
        self.connections: Optional[List[LinkConnectionSpec]] = None

    @property
    def alias(self) -> str:
        return self._alias or self.type

    @alias.setter
    def alias(self, value: Optional[str]) -> None:
        if value and value != self.type:
            self._alias = value
        else:
            self._alias = None

    @classmethod
    def from_dict(cls: Type[T], raw: Dict[str, Any]) -> T:
        link = cls(raw["type"])
        link._alias = raw.get("alias")

        if "connections" in raw:
            link.connections = LinkConnectionSpec.from_dict_all(raw["connections"])

        return link


class OutputLinkSpec(LinkSpec):
    def __init__(self, type: str) -> None:
        super().__init__(type)

        self.connect_all_from: Optional[Reference] = None

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "OutputLinkSpec":
        link = super(OutputLinkSpec, cls).from_dict(raw)

        if "connect_all_from" in raw:
            link.connect_all_from = Reference.parse(raw["connect_all_from"])

        return link


class InputLinkSpec(LinkSpec):
    def __init__(self, type: str) -> None:
        super().__init__(type)

        self.automatic: bool = False
        self.connect_all_to: Optional[Reference] = None
        self.multiple_target: Optional[Reference] = None
        self.params_connections: Optional[List[LinkConnectionSpec]] = None
        self.params_schema: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "InputLinkSpec":
        link = super(InputLinkSpec, cls).from_dict(raw)

        link.automatic = raw.get("automatic", link.automatic)

        if "connect_all_to" in raw:
            link.connect_all_to = Reference.parse(raw["connect_all_to"])

        if "multiple_target" in raw:
            link.multiple_target = Reference.parse(raw["multiple_target"])

        # TODO: param_connections and param_schema mutually inclusive. Raise error if only one set
        if "params_connections" in raw:
            link.params_connections = LinkConnectionSpec.from_dict_all(
                raw["params_connections"]
            )

        if "params_schema" in raw:
            params_schema = raw["params_schema"]
            schema.apply_default_schema(params_schema)
            link.params_schema = params_schema

        return link
