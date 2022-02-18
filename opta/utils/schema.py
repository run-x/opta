# new-module-api

import collections
import functools
from pathlib import Path
from typing import Any, Final

import jsonschema

from opta.utils import yaml

_ROOT_PATH: Final[Path] = Path(__file__).parent.parent.parent

ValidationError = jsonschema.ValidationError


def apply_default_schema(data: collections.abc.MutableMapping) -> None:
    defaults = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "$id": "https://test",
    }

    for key, value in defaults.items():
        data.setdefault(key, value)


def validate(data: Any, schema: Any) -> None:
    jsonschema.validate(data, schema)  # TODO: Custom class?


@functools.lru_cache
def module_schema() -> Any:
    schema_path = _ROOT_PATH.joinpath("schemas", "module.yaml")

    with open(schema_path, "r") as f:
        return yaml.load(f)


# Monkeypatch RefResolver so it never makes remote calls
def _resolve_remote(self: jsonschema.RefResolver, uri: str) -> Any:
    print("CALLED resolve_remote")
    raise NotImplementedError(f"Remote fetches disabled ({type(uri).__name__}: {uri})")


jsonschema.RefResolver.resolve_remote = _resolve_remote
