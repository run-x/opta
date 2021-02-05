import sys
from shutil import which
from typing import Any, Dict

from opta.special_formatter import PartialFormatter

fmt = PartialFormatter("")


def deep_merge(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    b = b.copy()
    for key, value in a.items():
        if key in b:
            if isinstance(value, dict) and isinstance(b[key], dict):
                b[key] = deep_merge(value, b[key])
            elif value != b[key]:
                raise Exception(f"Cant merge conflicting non-dict values (key: {key})")
        else:
            b[key] = value

    return b


def hydrate(target: Any, hydration: Dict[Any, Any]) -> Dict[Any, Any]:
    if isinstance(target, dict):
        target = target.copy()
        for k, v in target.items():
            target[k] = hydrate(v, hydration)
    elif isinstance(target, list):
        target = [hydrate(x, hydration) for x in target]
    elif isinstance(target, str):
        target = fmt.format(target, **hydration)

    return target


def is_tool(name: str) -> bool:
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None


def safe_run(func):  # type: ignore
    def func_wrapper(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if hasattr(sys, "_called_from_test"):
                raise e
            else:
                print(e)
                return None

    return func_wrapper


def fmt_msg(message: str) -> str:
    message = message.replace("\n", " ")
    while "  " in message:
        message = message.replace("  ", " ")
    message = message.replace("~", "\n")
    return message
