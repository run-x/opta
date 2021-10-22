"""
This module extends Python's built-in json module to add support for custom object encoding.
"""

import functools
import json
from typing import Any

# Re-export everything we don't modify
load = json.load
loads = json.loads
JSONDecoder = json.JSONDecoder
JSONDecodeError = json.JSONDecodeError


class JSONEncoder(json.JSONEncoder):
    """A JSON encoder that allows objects to specify how they are encoded by implementing a __to_json__ method"""

    def default(self, obj: Any) -> Any:
        if callable(getattr(obj, "__to_json__", None)):
            return obj.__to_json__()

        return super().default(obj)


dumps = functools.partial(json.dumps, cls=JSONEncoder)
dump = functools.partial(json.dump, cls=JSONEncoder)
