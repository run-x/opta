import pytest

from opta.utils.ref import (
    _INTERPOLATION_REGEX,
    _PART_REGEX,
    ComplexInterpolatedReference,
    Reference,
    SimpleInterpolatedReference,
)


class TestRef:
    def test_part_regex(self) -> None:
        assert _PART_REGEX.fullmatch("abc") is not None
        assert _PART_REGEX.fullmatch("a2_3") is not None
        assert _PART_REGEX.fullmatch("1abc") is None

    def test_interpolation_regex(self) -> None:
        assert _INTERPOLATION_REGEX.fullmatch("${foo}") is not None
        assert _INTERPOLATION_REGEX.fullmatch("${foo.bar}") is not None


class TestSimpleInterpolatedReference:
    def test_parse(self) -> None:
        assert SimpleInterpolatedReference.parse(
            "${foo.bar}"
        ) == SimpleInterpolatedReference("foo", "bar")

        # TODO: Test parse exception

    def test_str(self) -> None:
        assert str(SimpleInterpolatedReference("foo", "bar")) == "${foo.bar}"


class TestReference:
    def test_parse(self) -> None:
        assert Reference.parse("foo.bar") == Reference("foo", "bar")
        # TODO: Test parse exception

    def test_str(self) -> None:
        assert str(Reference("foo", "bar")) == "foo.bar"

    # TODO: Test __add__


class TestComplexInterpolatedReference:
    def test_components_to_str(self) -> None:
        input = "secure_${postgres.db}_read_${postgres.someparameter}"

        built = ComplexInterpolatedReference(
            [
                "secure_",
                SimpleInterpolatedReference("postgres", "db"),
                "_read_",
                SimpleInterpolatedReference("postgres", "someparameter"),
            ]
        )
        assert input == str(built)

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
        processed = str(ComplexInterpolatedReference.parse(input))
        assert input == processed
