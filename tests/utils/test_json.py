import io
import json as stdjson
from typing import Any

import pytest

from opta.utils import json


class SerializableType:
    def __init__(self, val: Any):
        self.val = val

    def __to_json__(self) -> Any:
        return self.val


class NonSerializableType:
    def __init__(self, val: Any):
        self.val = val


class TestEncoder:
    def test_default(self) -> None:
        encoder = json.JSONEncoder()
        val = SerializableType(1)

        assert encoder.default(val) == 1

    def test_not_jsonable(self) -> None:
        encoder = json.JSONEncoder()
        val = NonSerializableType(1)

        with pytest.raises(TypeError):
            encoder.default(val)


def test_dump() -> None:
    val = SerializableType(1)
    buf = io.StringIO()
    json.dump(val, buf)

    assert buf.getvalue() == "1"


def test_dumps() -> None:
    val = SerializableType(1)
    assert json.dumps(val) == "1"


def test_plain_encoding() -> None:
    val = {
        "abc": 123,
        "foo": "bar",
    }

    assert stdjson.dumps(val) == json.dumps(val)
