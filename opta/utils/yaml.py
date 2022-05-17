from __future__ import annotations

import pathlib
import warnings
from typing import IO, Any, Iterable, Optional, Union

import ruamel.yaml
from ruamel.yaml import YAML as lib_YAML

Loadable = Union[str, pathlib.Path, IO]


class YAML:
    """
    Wrapper class for ruamel.yaml.YAML
    """

    def __init__(self, *, base: Optional[lib_YAML] = None) -> None:
        """
        If a base ruamel.yaml.YAML instance is not passed, will default to a safe instance
        """
        self._base = base

    @classmethod
    def round_trip(cls, *, preserve_quotes: bool = False) -> YAML:
        base = cls._make_base("rt")
        base.preserve_quotes = preserve_quotes  # type: ignore[assignment]

        return cls(base=base)

    @classmethod
    def safe(cls) -> YAML:
        """
        Create a "safe" instance of the YAML loader/dumper.
        The bare constructor should be used instead, but this method is kept as a "reminder" for the developer
        """
        warnings.warn(
            f"Use {cls.__qualname__}() instead of {cls.__qualname__}.safe()",
            DeprecationWarning,
        )

        return cls(base=cls._make_base("safe"))

    @classmethod
    def unsafe(cls) -> YAML:
        """
        Creates an "unsafe" instance of the YAML loader/dumper.
        This should almost never be used, but is kept present so developers can be warned.
        """
        warnings.warn(
            f"{cls.__qualname__}.unsafe()should be avoided wherever possible",
            DeprecationWarning,
        )

        return cls(base=cls._make_base("unsafe"))

    @property
    def base(self) -> lib_YAML:
        """
        The underlying ruamel.yaml.YAML instance.
        """
        if not self._base:
            self._base = self._make_base("safe")

        return self._base

    def load(self, f: Loadable) -> Any:
        return self.base.load(f)

    def dump(self, data: Any, f: IO) -> None:
        self.base.dump(data, f)

    def dump_all(self, data: Iterable[Any], f: IO) -> None:
        self.base.dump_all(data, f)

    @property
    def explicit_start(self) -> bool:
        """
        If True, all dumped YAML documents start with an explicit start-of-document marker even if not necessary
        """
        return self.base.explicit_start or False

    @explicit_start.setter
    def explicit_start(self, value: bool) -> None:
        self.base.explicit_start = value  # type: ignore[assignment]

    @staticmethod
    def _make_base(type: str) -> lib_YAML:
        return lib_YAML(typ=type)


YAMLError = ruamel.yaml.YAMLError

_yaml = YAML()
dump = _yaml.dump
dump_all = _yaml.dump_all
load = _yaml.load
