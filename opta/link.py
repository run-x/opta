from typing import Any, Dict, Optional, Set, Union

RawLink = Union[str, Dict[str, Any]]


class Link:
    name: str  # Name of module we are linking to (required)
    types: Optional[Set[str]]  # List of link types or their aliases; if None, automatic
    params: Optional[Dict[str, Any]]

    def __init__(
        self,
        name: str,
        *,
        types: Optional[Set[str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.types = types
        self.params = params

    def add_type(self, type: str) -> None:
        if self.types is None:
            self.types = set()

        self.types.add(type)

    def params_for(self, type: str) -> Dict[str, Any]:
        if not self.params:
            return {}

        return self.params.get(type, {})

    @classmethod
    def from_dict(cls, raw: RawLink) -> "Link":
        # Handle simplified form of name
        if isinstance(raw, str):
            raw = {"name": raw}

        link = cls(raw["name"])

        if "types" in raw:
            link.types = set(raw["types"])

        if "params" in raw:
            link.params = raw["params"]

        return link

    def to_dict(self) -> Dict[str, Any]:
        raw: Dict[str, Any] = {
            "name": self.name,
        }

        if self.types is not None:
            raw["types"] = sorted(self.types)

        if self.params:
            raw["params"] = self.params

        return raw
