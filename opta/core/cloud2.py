# new-module-api

from typing import Any, Dict

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from opta.core.terraform2 import TerraformFile
from opta.layer2 import Layer
from opta.stubs import AWSProvider


class Cloud:
    def state_storage(self, layer: Layer) -> str:
        """
        Cloud-specific identifier for where state is stored.
        In AWS, this is an S3 bucket name.
        """
        return f"opta-tf-state-{layer.org_name}-{layer.name}"

    def verify_storage(self, layer: Layer) -> bool:
        """
        Validates state storage in this cloud provider
        """
        raise NotImplementedError()

    def configure_providers(self, file: TerraformFile, layer: Layer) -> None:
        raise NotImplementedError()


class AWS(Cloud):
    def verify_storage(self, layer: Layer) -> bool:
        bucket = self.state_storage(layer)
        provider_config = self._provider_config(layer)

        s3 = boto3.client("s3", config=Config(region_name=provider_config.region))
        try:
            s3.get_bucket_encryption(Bucket=bucket,)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return False
            raise e
        return True

    def configure_providers(self, file: TerraformFile, layer: Layer) -> None:
        config = self._provider_config(layer)

        # TODO: Support other, non-aws providers

        provider_config: Dict[str, Any] = {"region": config.region}
        if config.account_ids is not None:
            provider_config["allowed_account_ids"] = config.account_ids

        file.add_provider("aws", provider_config)

        # TODO: Upgraded from v3.58.0 to v3.73.0 to fix bug when creating routes (fixed in v3.70.0)
        file.add_required_provider(
            "aws", {"source": "hashicorp/aws", "version": "3.73.0"}
        )

        file.add_data("aws_caller_identity", "provider", {})
        file.add_data("aws_region", "provider", {})

    def _provider_config(self, layer: Layer) -> AWSProvider:
        provider_config = layer.providers.aws
        if not provider_config:
            raise ValueError("expected AWS provider config to be present")

        return provider_config
