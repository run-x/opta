import pytest

from opta.cloud.aws.config import AWSProviderConfig
from opta.exceptions import UserErrors


class TestAWSProviderConfig:
    def test_from_dict_no_region(self) -> None:
        with pytest.raises(UserErrors) as e:
            AWSProviderConfig.from_dict({})

        assert str(e.value) == "AWS region must be provided when using the AWS provider"

    def test_from_dict_no_account_id(self, raw: dict) -> None:
        config = AWSProviderConfig.from_dict(raw)

        assert config.account_ids is None

    def test_from_dict_empty_account_ids(self, raw: dict) -> None:
        raw["account_id"] = []

        config = AWSProviderConfig.from_dict(raw)

        assert config.account_ids == []

    def test_from_dict_str(self, raw: dict) -> None:
        raw["account_id"] = "123"

        config = AWSProviderConfig.from_dict(raw)

        assert config.account_ids == ["123"]

    def test_from_dict_int(self, raw: dict) -> None:
        raw["account_id"] = 123

        config = AWSProviderConfig.from_dict(raw)

        assert config.account_ids == ["123"]

    def test_from_dict(self, raw: dict) -> None:
        raw["account_id"] = ["123", "456"]

        config = AWSProviderConfig.from_dict(raw)

        assert config.region == "us-east-1"
        assert config.account_ids == ["123", "456"]

    @pytest.fixture
    def raw(self) -> dict:
        return {"region": "us-east-1"}
