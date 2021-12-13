from opta.utils.ref import _INTERPOLATION_REGEX, _PART_REGEX, InterpolatedReference, Reference


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
