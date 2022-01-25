import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from opta.core.terraform2 import TerraformFile
from opta.layer2 import Layer


class CloudProvider:
    def state_storage(self, layer: Layer) -> str:
        return f"opta-tf-state-{layer.org_name}-{layer.name}"

    def verify_storage(self, layer: Layer) -> bool:
        raise NotImplementedError()

    def add_provider_config(self, file: TerraformFile, layer: Layer) -> None:
        raise NotImplementedError()


class AWSProvider(CloudProvider):
    def verify_storage(self, layer: Layer) -> bool:
        bucket = self.state_storage(layer)
        region = "us-east-1"  # TODO: Read from provider data in layer

        s3 = boto3.client("s3", config=Config(region_name=region))
        try:
            s3.get_bucket_encryption(Bucket=bucket,)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return False
            raise e
        return True

    def add_provider_config(self, file: TerraformFile, layer: Layer) -> None:
        config = layer.providers.aws

        if not config:
            raise ValueError("expected AWS provider to be configured")

        # TODO: Support other, non-aws providers

        file.add_provider(
            "aws", {"region": config.region, "allowed_account_ids": config.account_ids}
        )

        # TODO: Upgraded from v3.58.0 to v3.73.0 to fix bug when creating routes (fixed in v3.70.0)
        file.add_required_provider(
            "aws", {"source": "hashicorp/aws", "version": "3.73.0"}
        )

        file.add_data("aws_caller_identity", "provider", {})
        file.add_data("aws_region", "provider", {})
