"""
This module extends Python's built-in json module to add support for custom object encoding.
"""
import json

# Re-export everything we don't modify
load = json.load
loads = json.loads
JSONDecoder = json.JSONDecoder
JSONDecodeError = json.JSONDecodeError


def dumps(*args, **kwargs):
    kwargs["cls"] = JSONEncoder

    return json.dumps(*args, **kwargs)

def dump(*args, **kwargs):
    kwargs["cls"] = JSONEncoder

    return json.dump(*args, **kwargs)


class JSONEncoder(json.JSONEncoder):
    """A JSON encoder that allows objects to specify how they are encoded by implementing a __to_json__ method"""

    def default(self, obj):
        if callable(getattr(obj, "__to_json__", None)):
            return obj.__to_json__()

        return super().default(obj)
