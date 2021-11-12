from typing import Dict, FrozenSet, Optional, Set, Union

from opta.exceptions import UserErrors
from opta.utils import is_tool

_registered_path_executables: Dict[str, Optional[str]] = {}

# TODO: In python 3.9+, switch to using collections.abc.Set
StringSetOrFrozen = Union[Set[str], FrozenSet[str]]


def get_missing_path_executables(names: StringSetOrFrozen) -> Dict[str, Optional[str]]:
    """
    Returns a dict whose keys are executables missing from the PATH, limited to `names`.
    The dict value, if not None, is the URL to the install page for that tool.
    """
    missing: Dict[str, Optional[str]] = {}

    for name in names:
        if is_tool(name):
            continue

        try:
            missing[name] = _registered_path_executables[name]
        except KeyError:
            raise ValueError(f"{name} is not a registered path executable")

    return missing


def register_path_executable(name: str, *, install_url: Optional[str] = None) -> None:
    """
    Registers an executable for later use in dependency checks.
    """
    if name in _registered_path_executables:
        raise ValueError(f"{name} already registered as a path executable")

    _registered_path_executables[name] = install_url


def validate_installed_path_executables(names: FrozenSet[str]) -> None:
    """Raises a UserErrors exception if any executables listed in `names` are missing from PATH"""
    missing = get_missing_path_executables(names)
    if not missing:
        return

    sorted_names = sorted(missing)

    nice_missing = [
        name + (f" (visit {missing[name]} to install)" if missing[name] else "")
        for name in sorted_names
    ]

    message = "Missing required executables on PATH: {}".format("; ".join(nice_missing))

    raise UserErrors(message)
