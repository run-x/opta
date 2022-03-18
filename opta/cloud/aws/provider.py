# new-module-api

from __future__ import annotations

from typing import Any, Dict

from opta.cloud.provider import CloudProvider
from opta.core.terraform2 import TerraformFile

from .config import AWSProviderConfig


class AWSProvider(CloudProvider):
    def __init__(self, config: AWSProviderConfig) -> None:
        self._config = config

    def configure_terraform_file(self, file: TerraformFile) -> None:
        provider_config: Dict[str, Any] = {"region": self._config.region}
        if self._config.account_ids is not None:
            provider_config["allowed_account_ids"] = self._config.account_ids

        file.add_provider("aws", provider_config)

        # TODO: Upgraded from v3.58.0 to v3.73.0 to fix bug when creating routes (fixed in v3.70.0)
        # TODO: Should this be pulled from config/registry/aws/index.yaml?
        file.add_required_provider(
            "aws", {"source": "hashicorp/aws", "version": "3.73.0"}
        )

        file.add_data("aws_caller_identity", "provider", {})
        file.add_data("aws_region", "provider", {})
