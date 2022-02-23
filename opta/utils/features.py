# new-module-api

import functools
import os

_FEATURE_MODULE_API_ENV = "OPTA_MODULE_API_ENABLED"


def is_module_api_enabled() -> bool:
    return _check_env(_FEATURE_MODULE_API_ENV)


@functools.lru_cache
def _check_env(key: str) -> bool:
    val = os.environ.get(key)
    if not val:
        return False

    true_values = [
        "true",
        "1",
        "yes",
        "y",
    ]

    return val.lower() in true_values
