from shutil import which
from typing import Any, Dict


def deep_merge(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    b = b.copy()
    for key, value in a.items():
        if key in b:
            if isinstance(value, dict) and isinstance(b[key], dict):
                b[key] = deep_merge(value, b[key])
            elif value != b[key]:
                raise Exception("Cant merge dict with non dict")
        else:
            b[key] = value

    return b


def hydrate(target: Dict[Any, Any], hydration: Dict[Any, Any]) -> Dict[Any, Any]:
    target = target.copy()

    for k, v in target.items():
        if isinstance(v, str):
            target[k] = v.format(**hydration)
        elif isinstance(v, dict):
            target[k] = hydrate(v, hydration)

    return target


def is_tool(name: str):
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None
