import io

import pytest

from opta.utils import json

class SerializableType:
    def __init__(self, val):
        self.val = val

    def __to_json__(self):
        return self.val

class NonSerializableType:
    def __init__(self, val):
        self.val = val

class TestEncoder:
    def test_default(self):
        encoder = json.JSONEncoder()
        val = SerializableType(1)

        assert encoder.default(val) == 1

    def test_not_jsonable(self):
        encoder = json.JSONEncoder()
        val = NonSerializableType(1)

        with pytest.raises(TypeError):
            encoder.default(val)


def test_dump():
    val = SerializableType(1)
    buf = io.StringIO()
    json.dump(val, buf)

    assert buf.getvalue() == "1"

def test_dumps():
    val = SerializableType(1)
    assert json.dumps(val) == "1"
