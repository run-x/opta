from opta.utils.ref import (
    _INTERPOLATION_REGEX,
    _PART_REGEX,
    ComplexInterpolatedReference,
    InterpolatedReference,
    Reference,
)


class TestRef:
    def test_part_regex(self) -> None:
        assert _PART_REGEX.fullmatch("abc") is not None
        assert _PART_REGEX.fullmatch("a2_3") is not None
        assert _PART_REGEX.fullmatch("1abc") is None

    def test_interpolation_regex(self) -> None:
        assert _INTERPOLATION_REGEX.fullmatch("${foo}") is not None
        assert _INTERPOLATION_REGEX.fullmatch("${foo.bar}") is not None


class TestInterpolatedReference:
    def test_parse(self) -> None:
        assert InterpolatedReference.parse("${foo.bar}") == InterpolatedReference(
            "foo", "bar"
        )

        # TODO: Test parse exception

    def test_str(self) -> None:
        assert str(InterpolatedReference("foo", "bar")) == "${foo.bar}"


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

        built = ComplexInterpolatedReference([
            "secure_", 
            InterpolatedReference("postgres","db"),
            "_read_",
            InterpolatedReference("postgres","someparameter")
            ])
        assert(input == str(built))
            

    def test_parse_and_str(self) -> None:
        input = "secure_${postgres.db}_read_${postgres.someparameter}"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = "${postgres.db}_read_${postgres.someparameter}"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = "${postgres.someparameter}"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = "${postgres.db}_read"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = "${postgres.db}${postgres.someparameter}"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = "onlyliteral"
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

        input = ""
        processed =  str(ComplexInterpolatedReference.parse(input))
        assert(input==processed)

