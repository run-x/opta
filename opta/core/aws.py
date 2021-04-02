from time import sleep
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer


class AWS:
    def __init__(self, layer: "Layer"):
        self.layer = layer
        providers = layer.root().gen_providers(0)["provider"]
        self.region = providers["aws"]["region"]

    # Fetches AWS resources tagged with "opta: true"
    # Works on most resources, but not all (ex. IAM, elasticache subnet groups)
    # Unfortunately this is the best single API to get AWS resources, since there's
    # no API that can fetch all resources.
    #
    # The returned structure is
    # {
    #    "terraform.address" : "aws resource arn"
    # }
    def get_opta_resources(self) -> dict:
        client = boto3.client(
            "resourcegroupstaggingapi", config=Config(region_name=self.region)
        )

        state = client.get_resources(
            TagFilters=[
                {"Key": "opta", "Values": ["true"]},
                {"Key": "layer", "Values": [self.layer.name]},
            ]
        )
        resources = state["ResourceTagMappingList"]

        resources_map = {}
        for resource in resources:
            arn = resource["ResourceARN"]
            for tag in resource["Tags"]:
                if tag["Key"] == "tf_address":
                    terraform_address = tag["Value"]
                    resources_map[terraform_address] = arn

        return resources_map

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self, config: str) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        s3_client.upload_file(config, bucket, config_path)
        logger.debug("Uploaded opta config to s3")

    def delete_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        resp = s3_client.delete_object(Bucket=bucket, Key=config_path)

        if resp["ResponseMetadata"]["HTTPStatusCode"] != 204:
            raise Exception(f"Failed to delete opta config in {bucket}/{config_path}.")

        logger.info("Deleted opta config from s3")

    @staticmethod
    def delete_bucket(bucket_name: str) -> None:
        # Before a bucket can be deleted, all of the objects inside must be removed.
        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.objects.all().delete()

        # Delete the bucket itself
        client = boto3.client("s3")
        client.delete_bucket(Bucket=bucket_name)
        print(f"Bucket ({bucket_name}) successfully deleted.")

    @staticmethod
    def delete_dynamodb_table(table_name: str, region: str) -> None:
        client = boto3.client("dynamodb", config=Config(region_name=region))

        for _ in range(20):
            try:
                client.delete_table(TableName=table_name)
                print(f"DynamoDB table ({table_name}) successfully deleted.")
                return None
            except client.exceptions.ResourceInUseException:
                logger.info(
                    fmt_msg(
                        """
                        The dynamodb table is currently being created/updated.
                        ~Please wait for deletion to retry..
                    """
                    )
                )
                sleep(5)

        raise Exception("Failed to delete after 20 retries, quitting.")


# AWS Resource ARNs can be one of the following 3 formats:
# 1). arn:partition:service:region:account-id:resource-id
# 2). arn:partition:service:region:account-id:resource-type/resource-id
# 3). arn:partition:service:region:account-id:resource-type:resource-id
def get_aws_resource_id(resource_arn: str) -> str:
    arn_parts = resource_arn.split(":")

    # Format 1:
    if len(arn_parts) == 6 and "/" not in arn_parts[-1]:
        return arn_parts[-1]

    # Format 2
    if len(arn_parts) == 6 and "/" in arn_parts[-1]:
        return arn_parts[-1].split("/")[1]

    # Format 3
    if len(arn_parts) == 7:
        return arn_parts[-1]

    raise Exception(f"Not a valid AWS arn: {resource_arn}")
