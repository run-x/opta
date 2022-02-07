import io
from typing import Any, List

import pytest

from opta.utils.ref import (
    _COMPLEX_SPLIT_REGEX,
    _INTERPOLATION_REGEX,
    _PART_INT_REGEX,
    _PART_REGEX,
    _PART_STR_REGEX,
    _SIMPLE_INTERPOLATION_REGEX,
)
from opta.utils.ref import ComplexInterpolatedReference as Complex
from opta.utils.ref import Reference, ReferenceParseError
from opta.utils.ref import SimpleInterpolatedReference as Simple
from opta.utils.ref import get_all_references, is_interpolated_reference, parse_ref_string
from opta.utils.yaml import dump, load


class TestRegex:
    def test_part_str_regex(self) -> None:
        assert _PART_STR_REGEX.fullmatch("abc") is not None
        assert _PART_STR_REGEX.fullmatch("a2_3") is not None
        assert _PART_STR_REGEX.fullmatch("1abc") is None

    def test_part_int_regex(self) -> None:
        assert _PART_INT_REGEX.fullmatch("1") is not None
        assert _PART_INT_REGEX.fullmatch("10") is not None
        assert _PART_INT_REGEX.fullmatch("01") is None
        assert _PART_INT_REGEX.fullmatch("-1") is None

    def test_part_regex(self) -> None:
        assert _PART_REGEX.fullmatch("1v") is None

    def test_interpolation_regex(self) -> None:
        assert _INTERPOLATION_REGEX.fullmatch("${foo}") is not None
        assert _INTERPOLATION_REGEX.fullmatch("${foo.bar}") is not None

    def test_simple_interpolation_regex(self) -> None:
        assert _SIMPLE_INTERPOLATION_REGEX.fullmatch("${abc[123]}") is not None
        assert _SIMPLE_INTERPOLATION_REGEX.fullmatch("${foo + bar + 1}") is not None
        assert _SIMPLE_INTERPOLATION_REGEX.fullmatch("{abc}") is None

    def test_complex_split_regex(self) -> None:
        m = _COMPLEX_SPLIT_REGEX.fullmatch("${abc}")
        assert m is not None
        assert m.group(1) == "${abc}"


class TestReference:
    def test_parse(self, ref1: Reference) -> None:
        assert Reference.parse("a.1.x") == ref1

    def test_parse_invalid(self) -> None:
        with pytest.raises(ReferenceParseError):
            Reference.parse("!")

        with pytest.raises(ReferenceParseError):
            Reference.parse("1a")

    def test_str(self) -> None:
        assert str(Reference("foo", "bar")) == "foo.bar"

    def test_repr(self) -> None:
        assert repr(Reference("foo", 1, "bar")) == "Reference('foo', 1, 'bar')"

    def test_lt(self, ref1: Reference, ref2: Reference) -> None:
        assert ref1 < ref2

    def test_lt_invalid_type(self, ref1: Reference) -> None:
        with pytest.raises(TypeError):
            ref1 < 5

    def test_eq_same(self, ref1: Reference) -> None:
        ref2 = ref1.child()

        assert ref1 is not ref2
        assert ref1 == ref2

    def test_eq_different(self, ref1: Reference, ref2: Reference) -> None:
        assert ref1 != ref2

    def test_getitem_single(self, ref1: Reference, ref2: Reference) -> None:
        assert ref1[0] == "a"
        assert ref1[1] == 1
        assert ref2[1] == 2

    def test_getitem_slice(self, ref1: Reference) -> None:
        assert ref1[1:3] == Reference(1, "x")

    def test_getitem_invalid_type(self, ref1: Reference) -> None:
        with pytest.raises(TypeError):
            ref1["foo"]  # type: ignore

    def test_iter(self, ref1: Reference) -> None:
        it = list(ref1.__iter__())

        assert it == ["a", 1, "x"]

    def test_len(self, ref1: Reference) -> None:
        assert len(ref1) == 3

    def test_hash(self, ref1: Reference) -> None:
        # We don't test the actual value since it changes in every Python process
        # and we don't really care what it actually is, just that the method works
        assert isinstance(ref1.__hash__(), int)

    def test_add_ref(self, ref1: Reference, ref2: Reference, ref1_2: Reference) -> None:
        assert ref1 + ref2 == ref1_2

    def test_add_iterable(self, ref1: Reference) -> None:
        assert ref1 + ["b"] == Reference("a", 1, "x", "b")

    def test_child(self, ref1: Reference) -> None:
        new = ref1.child("foo", "bar")
        assert new is not ref1
        assert new == Reference("a", 1, "x", "foo", "bar")

    def test_join(self, ref1: Reference, ref2: Reference, ref1_2: Reference) -> None:
        new = ref1.join(ref2)
        assert new is not ref1
        assert new is not ref2

        assert new == ref1_2

    def test_path(self, ref1: Reference) -> None:
        path = ref1.path

        assert isinstance(path, tuple)
        assert path == ("a", 1, "x")

    def test_validate_path(self) -> None:
        with pytest.raises(ValueError):
            Reference(-1)

        with pytest.raises(ValueError):
            Reference("1")

        with pytest.raises(TypeError):
            Reference(1.2)  # type: ignore

    @pytest.fixture
    def ref1(self) -> Reference:
        return Reference("a", 1, "x")

    @pytest.fixture
    def ref2(self) -> Reference:
        return Reference("a", 2, "y")

    @pytest.fixture
    def ref1_2(self) -> Reference:
        "ref1 concatenated with ref2"
        return Reference("a", 1, "x", "a", 2, "y")


class TestSimpleInterpolatedReference:
    def test_parse(self, ref1: Simple) -> None:
        assert Simple.parse("${a.1.x}") == ref1

    @pytest.mark.parametrize("input", ["foo.bar", "{foo}", "${21b}", "${-1}"])
    def test_parse_fail(self, input: str) -> None:
        with pytest.raises(ReferenceParseError):
            Simple.parse(input)

    def test_str(self, ref1: Simple) -> None:
        assert str(ref1) == "${a.1.x}"

    def test_ref(self, ref1: Simple) -> None:
        ref = ref1.ref
        assert ref.__class__ is Reference
        assert ref == Reference("a", 1, "x")

    def test_parse_dotted(self, ref1: Simple) -> None:
        parsed = Simple.parse_dotted("a.1.x")
        assert parsed == ref1

    def test_to_yaml(self, ref1: Simple) -> None:
        expected = "!ref a.1.x\n...\n"

        buf = io.BytesIO()
        dump(ref1, buf)

        actual = buf.getvalue().decode("utf-8")
        assert actual == expected

    def test_from_yaml(self, ref1: Simple) -> None:
        input = "!ref a.1.x".encode("utf-8")
        buf = io.BytesIO(input)
        actual = load(buf)

        assert actual == ref1

    @pytest.fixture
    def ref1(self) -> Simple:
        return Simple("a", 1, "x")


class TestComplexInterpolatedReference:
    def test_components_to_str(self) -> None:
        input = "secure_${postgres.db}_read_${postgres.someparameter}"

        built = Complex(
            "secure_",
            Simple("postgres", "db"),
            "_read_",
            Simple("postgres", "someparameter"),
        )
        assert input == str(built)

    @pytest.mark.parametrize(
        ["input", "expected"],
        [["foo${bar}${spam}", [Reference("bar"), Reference("spam")]], ["foo", []]],
    )
    def test_refs(self, input: str, expected: List[Reference]) -> None:
        ref = Complex.parse(input)
        print(ref._parts)
        refs = ref.refs

        assert refs == expected

    @pytest.mark.parametrize(
        "input",
        [
            "abc_${foo.bar}xyz${spam.ham}",
            "${foo.bar}xyz${spam.ham}",
            "${foo.bar}",
            "${foo.bar}_abc",
            "${foo.bar}${spam.ham}",
            "abc",
            "",
        ],
    )
    def test_parse_and_str_roundtrip(self, input: str) -> None:
        ref = Complex.parse(input)
        processed = str(ref)
        assert input == processed


class TestFuncs:
    @pytest.mark.parametrize(
        ["input", "expected"],
        [
            ["${foo}", Simple("foo")],
            ["foo", "foo"],
            ["${foo}bar", Complex(Simple("foo"), "bar")],
        ],
    )
    def test_parse_ref_string(self, input: str, expected: Any) -> None:
        assert parse_ref_string(input) == expected

    @pytest.mark.parametrize(
        ["input", "expected"],
        [
            ["foo", False],
            [Reference("foo"), False],
            [Simple("foo"), True],
            [Complex.parse("foo"), True],
            [Complex("foo"), True],
        ],
    )
    def test_is_interpolated_reference(self, input: Any, expected: bool) -> None:
        assert is_interpolated_reference(input) == expected

    @pytest.mark.parametrize(
        ["input", "expected"],
        [
            ["foo", []],
            [Simple("foo"), [Simple("foo")]],
            [Complex.parse("foo${bar}${spam}"), [Simple("bar"), Simple("spam")]],
        ],
    )
    def test_get_all_references(self, input: Any, expected: List[Reference]) -> None:
        actual = get_all_references(input)

        assert actual == expected
