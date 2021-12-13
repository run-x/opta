from typing import Optional, Type

import pytest

from opta.preprocessor.v1 import reformat_interpolation


class TestInterpolation:
    def reformat_interpolation_assert(
        self,
        input: str,
        *,
        expected: Optional[str] = None,
        exception_type: Optional[Type[Exception]] = None,
        exception_message: Optional[str] = None,
    ) -> None:
        if exception_type:
            with pytest.raises(exception_type) as e:
                output = reformat_interpolation(input)

            if exception_message is not None:
                assert str(e.value) == exception_message
        else:
            output = reformat_interpolation(input)

        assert output == expected

    @pytest.mark.parametrize(
        "input,expected",
        [
            ["foo", "foo"],
            ["foo {bar}", "foo ${bar}"],
            ["{spam} {ham}", "${spam} ${ham}"],
            ["${foo}", "$${foo}"],
        ],
    )
    def test_reformat_interpolation_good(self, input: str, expected: str) -> None:
        self.reformat_interpolation_assert(input, expected=expected)
