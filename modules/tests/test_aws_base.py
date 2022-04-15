from typing import Any, Dict, Final, List

import pytest
from pytest_mock import MockFixture

from modules.aws_base.aws_base import AwsBaseProcessor
from opta.exceptions import UserErrors

_MODULE_PATH: Final = "modules.aws_base.aws_base"
_DEBUG_PATH: Final = _MODULE_PATH + ".logger.debug"


class TestAwsBaseProcessor:
    def test_validate_existing_vpc_params(
        self,
        mocker: MockFixture,
        processor: AwsBaseProcessor,
        existing_vpc_config: Dict[str, Any],
    ) -> None:
        mock_debug = mocker.patch(_DEBUG_PATH)

        processor.validate_existing_vpc_params(existing_vpc_config)
        mock_debug.assert_called_once()

    @pytest.mark.parametrize(
        "missing",
        [
            ["vpc_id"],
            ["public_subnet_ids"],
            ["private_subnet_ids"],
            ["public_subnet_ids", "private_subnet_ids"],
        ],
    )
    def test_validate_existing_vpc_params_missing(
        self,
        mocker: MockFixture,
        processor: AwsBaseProcessor,
        existing_vpc_config: Dict[str, Any],
        missing: List[str],
    ) -> None:
        mock_debug = mocker.patch(_DEBUG_PATH)

        for key in missing:
            del existing_vpc_config[key]

        with pytest.raises(UserErrors) as e:
            processor.validate_existing_vpc_params(existing_vpc_config)

        mock_debug.assert_called_once()

        expected_message = f"In the aws_base module, the parameters `{', '.join(missing)}` are all required if any are set"
        assert str(e.value) == expected_message

    @pytest.mark.parametrize("duplicate", ["public_subnet_ids", "private_subnet_ids"])
    def test_validate_existing_vpc_params_nonunique(
        self,
        mocker: MockFixture,
        processor: AwsBaseProcessor,
        existing_vpc_config: Dict[str, Any],
        duplicate: str,
    ) -> None:
        mock_debug = mocker.patch(_DEBUG_PATH)

        # Make all the values in the key equal to the first value
        values: List[str] = existing_vpc_config[duplicate]
        existing_vpc_config[duplicate] = [values[0] for _ in values]

        with pytest.raises(UserErrors) as e:
            processor.validate_existing_vpc_params(existing_vpc_config)

        mock_debug.assert_called_once()

        expected_message = (
            f"In the aws_base module, the values in {duplicate} must all be unique"
        )
        assert str(e.value) == expected_message

    @pytest.fixture
    def processor(self) -> AwsBaseProcessor:
        return AwsBaseProcessor(None, None)  # typing: ignore

    @pytest.fixture
    def existing_vpc_config(self) -> Dict[str, Any]:
        return {
            "vpc_id": "vpc-123",
            "public_subnet_ids": ["subnet-abc", "subnet-def"],
            "private_subnet_ids": ["subnet-uvw", "subnet-xyz"],
        }
