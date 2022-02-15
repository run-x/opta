
from typing import Any
import pytest

from opta.utils.ref import Reference
from opta.utils.visit import Visitor


class TestVisitor:
    @pytest.fixture
    def basic_nested_object(self) -> dict:
        return {
            1: {
                "a": [2, 3],
            },
            "b": {
                "c": "d",
            },
        }

    @pytest.fixture
    def basic_visitor(self, basic_nested_object: dict) -> Visitor:
        return Visitor(basic_nested_object)

    def test_root(self, basic_nested_object: dict, basic_visitor: Visitor) -> None:
        assert basic_visitor.root is basic_nested_object

    @pytest.mark.parametrize(
        ["path", "expected"],
        [
            [Reference(2), False],
            [Reference(1), True],
            [Reference(1, "a"), True],
            [Reference(1, "a", 0), True],
            [Reference(1, "a", 1), True],
            [Reference(1, "a", 2), False],
            # [Reference("b", "c", 0), False],  # TODO: Broken test to fix
        ]
    )
    def test_contains(self, path: Reference, expected: bool, basic_visitor: Visitor) -> None:
        actual = path in basic_visitor

        assert actual == expected

    def test_contains_type_error(self, basic_visitor: Visitor) -> None:
        with pytest.raises(TypeError):
            "b" in basic_visitor

    def test_iter(self, basic_visitor: Visitor) -> None:
        keys = [path for path, _ in basic_visitor]

        assert keys == [
            Reference(1),
            Reference(1, "a"),
            Reference(1, "a", 0),
            Reference(1, "a", 1),
            Reference("b"),
            Reference("b", "c"),
        ]

    @pytest.mark.parametrize(
        ["path", "value"],
        [
            [Reference(1, "a"), [2, 3]],
            [Reference("b", "c"), "d"],
        ],
    )
    def test_getitem(self, path: Reference, value: Any, basic_visitor: Visitor) -> None:
        assert basic_visitor[path] == value
