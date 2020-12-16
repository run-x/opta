from typing import Any

from runxc.cli import collect_outputs


def test_output_collection() -> None:
    test_cases: Any = [
        ({"outputs": {"a": "b"}}, {"a": "b"}, {}),
        (
            {"outputs": {"a": "b"}, "submodules": [{"outputs": {"c": "d"}}]},
            {"a": "b", "c": "d"},
            {},
        ),
        ({"outputs": {"a": "b{d}2"}}, {"a": "be2"}, {"d": "e"}),
        ({"outputs": {"a": "b{d}2{e}"}}, {"a": "be2p"}, {"d": "e", "e": "p"}),
        (
            {
                "outputs": {"a": "b"},
                "arguments": {"a": "1"},
                "submodules": [{"outputs": {"c": "d{a}"}}],
            },
            {"a": "b", "c": "d1"},
            {},
        ),
    ]

    for (i, o, a) in test_cases:
        assert collect_outputs(i, a) == o
