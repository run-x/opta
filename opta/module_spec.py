# new-module-api

from __future__ import annotations

from typing import Any, Dict, List, Optional

from opta.link_spec import LinkConnectionSpec

SPEC_NAME = "module.yaml"


class ModuleSpec:
    """
    Type describing the specification of a module type, shared between instances of that module
    """

    name: str
    clouds: List[str]
    input_terraform_connections: List[LinkConnectionSpec]
    dir: Optional[str]

    @classmethod
    def from_dict(cls, dir: str, raw: Dict[str, Any]) -> ModuleSpec:
        spec = cls()
        spec.dir = dir
        spec.name = raw["name"]
        spec.clouds = raw["clouds"]

        spec.input_terraform_connections = [
            LinkConnectionSpec.from_dict(raw_conn)
            for raw_conn in raw.get("input_terraform_connections", [])
        ]

        return spec
