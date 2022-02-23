# new-module-api

import pytest

from opta.utils.ref import _PART_STR_REGEX, Reference, ReferenceParseError


class TestRegex:
    def test_part_str_regex(self) -> None:
        assert _PART_STR_REGEX.fullmatch("abc") is not None
        assert _PART_STR_REGEX.fullmatch("a2_3") is not None
        assert _PART_STR_REGEX.fullmatch("1abc") is None


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
