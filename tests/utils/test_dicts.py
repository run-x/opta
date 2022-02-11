from opta.utils import dicts


def test_extract() -> None:
    val = {
        "abc": 123,
        "foo": "bar",
    }

    assert dicts.extract(val, "unknown") == (val, {})
    assert dicts.extract(val, "foo") == ({"abc": 123}, {"foo": "bar"})
    assert val == {
        "abc": 123,
        "foo": "bar",
    }


def test_denormalize() -> None:
    val = {
        "abc": 123,
        "foo": "bar",
    }
    assert dicts.denormalize(val) == [{"abc": 123}, {"foo": "bar"}]
    val = {
        "module": {
            "base": {"description": "base module"},
            "k8s-cluster": {"description": "k8s module"},
        }
    }
    assert dicts.denormalize(val) == [
        {"module": {"base": {"description": "base module"}}},
        {"module": {"k8s-cluster": {"description": "k8s module"}}},
    ]


def test_merge() -> None:
    assert dicts.merge({"a": "aaa"}, {"b": "bbb"}) == {"a": "aaa", "b": "bbb"}
    d1 = {"output": {"name1": {"value": "value1"}, "name-both": {"value": "value1"}}}
    d2 = {"output": {"name2": {"value": "value2"}, "name-both": {"value": "value2"}}}
    assert dicts.merge(d1, d2) == {
        "output": {
            "name1": {"value": "value1"},
            # if a value is in both, takes the one from the first param
            "name-both": {"value": "value1"},
            "name2": {"value": "value2"},
        }
    }
