# new-module-api

from typing import Any, Dict, Iterable, List, Optional, TypeVar

from opta.link_spec import InputLinkSpec, LinkConnectionSpec, LinkSpec, OutputLinkSpec

SPEC_NAME = "module.yaml"

Schema = Dict[str, Any]
_T_LinkSpec = TypeVar("_T_LinkSpec", bound=LinkSpec)


class ModuleSpec:
    """
    Type describing the specification of a module type, shared between instances of that module
    """

    name: str
    clouds: List[str]
    input_schema: Schema
    input_links: List[InputLinkSpec]
    input_terraform_connections: List[LinkConnectionSpec]
    output_schema: Schema
    output_links: List[OutputLinkSpec]
    dir: Optional[str]

    def input_link_spec_for(self, type_or_alias: str) -> InputLinkSpec:
        return self._link_spec_for("Input", self.input_links, type_or_alias)

    def output_link_spec_for(self, type_or_alias: str) -> OutputLinkSpec:
        return self._link_spec_for("Output", self.output_links, type_or_alias)

    def _link_spec_for(
        self, type_name: str, specs: Iterable[_T_LinkSpec], type_or_alias: str
    ) -> _T_LinkSpec:
        try:
            return next(
                spec
                for spec in specs
                if spec.type == type_or_alias or spec.alias == type_or_alias
            )
        except StopIteration:
            raise KeyError(f"{type_name} link type/alias {type} not found.") from None

    @classmethod
    def from_dict(cls, dir: str, raw: Dict[str, Any]) -> "ModuleSpec":
        spec = cls()
        spec.dir = dir
        spec.name = raw["name"]
        spec.clouds = raw["clouds"]

        spec.input_schema = raw.get("input_schema", {})
        spec.output_schema = raw.get("output_schema", {})

        spec.input_links = [
            InputLinkSpec.from_dict(raw_link) for raw_link in raw.get("input_links", [])
        ]
        spec.output_links = [
            OutputLinkSpec.from_dict(raw_link) for raw_link in raw.get("output_links", [])
        ]

        spec.input_terraform_connections = [
            LinkConnectionSpec.from_dict(raw_conn)
            for raw_conn in raw.get("input_terraform_connections", [])
        ]

        return spec
