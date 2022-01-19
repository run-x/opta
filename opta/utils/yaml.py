from typing import IO, Any, Set, Type

from ruamel.yaml import YAML as lib_YAML

_yaml_classes: Set[Type] = set()


def YAML() -> lib_YAML:
    y = lib_YAML()
    y.indent(mapping=2, sequence=4, offset=2)

    for cls in _yaml_classes:
        y.register_class(cls)

    return y


def register_yaml_class(cls: Type) -> None:
    _yaml_classes.add(cls)


def load(f: IO) -> Any:
    y = YAML()

    return y.load(f)
