from typing import List, Optional

import pytest

from opta.cloud.aws.config import AWSProviderConfig
from opta.cloud.aws.provider import AWSProvider
from opta.core.terraform2 import TerraformFile


class TestAWSProvider:
    @pytest.mark.parametrize("account_ids", [None, ["123"]])
    def test_configure_terraform_file(
        self, account_ids: Optional[List[str]], config: AWSProviderConfig
    ) -> None:
        config.account_ids = account_ids[:] if account_ids else None

        actual = TerraformFile()
        provider = AWSProvider(config)

        provider.configure_terraform_file(actual)

        expected = TerraformFile()
        expected.providers = {"aws": {"region": "us-west-1"}}
        if account_ids is not None:
            expected.providers["aws"]["allowed_account_ids"] = account_ids
        expected.required_providers = {
            "aws": {"source": "hashicorp/aws", "version": "3.73.0"}
        }
        expected.data = {
            "aws_caller_identity": {"provider": {}},
            "aws_region": {"provider": {}},
        }

        assert actual.__to_json__() == expected.__to_json__()

    @pytest.fixture
    def config(self) -> AWSProviderConfig:
        config = AWSProviderConfig("us-west-1")

        return config
