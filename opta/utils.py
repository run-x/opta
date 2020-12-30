from typing import Any, Dict, Mapping


def deep_merge(a: Mapping[Any, Any], b: Dict[Any, Any]) -> Mapping[Any, Any]:
    b = b.copy()
    for key, value in a.items():
        if key in b:
            if isinstance(value, dict) and isinstance(b[key], dict):
                b[key] = deep_merge(value, b[key])
            else:
                raise Exception("Cant merge dict with non dict")
        else:
            b[key] = value

    return b
