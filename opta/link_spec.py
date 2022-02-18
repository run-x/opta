# new-module-api
"""
Classes defining the specs for links
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from opta.utils.ref import Reference


@dataclass  # TODO: In Python 3.10, pass in kw_only=True
class LinkConnectionSpec:
    source: Reference
    target: Reference

    @classmethod
    def from_dict(cls, raw: Dict[str, str]) -> LinkConnectionSpec:
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
    def from_dict_all(cls, raw_all: List[Dict[str, str]]) -> List[LinkConnectionSpec]:
        return [cls.from_dict(raw) for raw in raw_all]
