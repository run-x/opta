import json
from time import sleep
from typing import TYPE_CHECKING, List, Optional, TypedDict

import boto3
from botocore.config import Config
from mypy_boto3_dynamodb import DynamoDBClient

from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class AwsArn(TypedDict):
    arn: str
    partition: str
    service: str
    region: str
    account: str
    resource: str
    resource_type: Optional[str]


class AWS:
    def __init__(self, layer: "Layer"):
        self.layer = layer
        self.region = layer.root().providers["aws"]["region"]

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

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        try:
            obj = s3_client.get_object(Bucket=bucket, Key=config_path)
            return json.loads(obj["Body"].read())
        except Exception:  # Backwards compatibility
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        s3_client.put_object(
            Body=json.dumps(self.layer.structured_config()).encode("utf-8"),
            Bucket=bucket,
            Key=config_path,
        )
        logger.debug("Uploaded opta config to s3")

    def delete_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        resp = s3_client.delete_object(Bucket=bucket, Key=config_path)

        if resp["ResponseMetadata"]["HTTPStatusCode"] != 204:
            raise Exception(f"Failed to delete opta config in {bucket}/{config_path}.")

        logger.info("Deleted opta config from s3")

    def delete_remote_state(self) -> None:
        bucket = self.layer.state_storage()
        providers = self.layer.gen_providers(0)
        dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]

        dynamodb_client: DynamoDBClient = boto3.client(
            "dynamodb", config=Config(region_name=self.region)
        )
        dynamodb_client.delete_item(
            TableName=dynamodb_table,
            Key={"LockID": {"S": f"{bucket}/{self.layer.name}-md5"}},
        )

        s3_client = boto3.client("s3")
        resp = s3_client.delete_object(Bucket=bucket, Key=self.layer.name)

        if resp["ResponseMetadata"]["HTTPStatusCode"] != 204:
            raise Exception(
                f"Failed to delete opta tf state in {bucket}/{self.layer.name}."
            )
        logger.info(f"Deleted opta tf state for {self.layer.name}")

    @staticmethod
    def prepare_read_buckets_iam_statements(bucket_names: List[str]) -> dict:
        return {
            "Sid": "ReadBuckets",
            "Action": ["s3:GetObject*", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": [f"arn:aws:s3:::{bucket_name}" for bucket_name in bucket_names]
            + [f"arn:aws:s3:::{bucket_name}/*" for bucket_name in bucket_names],
        }

    @staticmethod
    def prepare_write_buckets_iam_statements(bucket_names: List[str]) -> dict:
        return {
            "Sid": "WriteBuckets",
            "Action": [
                "s3:GetObject*",
                "s3:PutObject*",
                "s3:DeleteObject*",
                "s3:ListBucket",
            ],
            "Effect": "Allow",
            "Resource": [f"arn:aws:s3:::{bucket_name}" for bucket_name in bucket_names]
            + [f"arn:aws:s3:::{bucket_name}/*" for bucket_name in bucket_names],
        }

    @staticmethod
    def prepare_publish_queues_iam_statements(queue_arns: List[str]) -> dict:
        return {
            "Sid": "PublishQueues",
            "Action": [
                "sqs:SendMessage",
                "sqs:SendMessageBatch",
                "sqs:GetQueueUrl",
                "sqs:GetQueueAttributes",
                "sqs:DeleteMessageBatch",
                "sqs:DeleteMessage",
            ],
            "Effect": "Allow",
            "Resource": [queue_arn for queue_arn in queue_arns],
        }

    @staticmethod
    def prepare_subscribe_queues_iam_statements(queue_arns: List[str]) -> dict:
        return {
            "Sid": "SubscribeQueues",
            "Action": ["sqs:ReceiveMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes"],
            "Effect": "Allow",
            "Resource": [queue_arn for queue_arn in queue_arns],
        }

    @staticmethod
    def prepare_publish_sns_iam_statements(topic_arns: List[str]) -> dict:
        return {
            "Sid": "PublishSns",
            "Action": ["sns:Publish"],
            "Effect": "Allow",
            "Resource": [topic_arn for topic_arn in topic_arns],
        }

    @staticmethod
    def prepare_kms_write_keys_statements(kms_arns: List[str]) -> dict:
        return {
            "Sid": "KMSWrite",
            "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
            "Effect": "Allow",
            "Resource": [kms_arn for kms_arn in kms_arns],
        }

    @staticmethod
    def prepare_kms_read_keys_statements(kms_arns: List[str]) -> dict:
        return {
            "Sid": "KMSRead",
            "Action": ["kms:Decrypt"],
            "Effect": "Allow",
            "Resource": [kms_arn for kms_arn in kms_arns],
        }

    @staticmethod
    def delete_bucket(bucket_name: str) -> None:
        # Before a bucket can be deleted, all of the objects inside must be removed.
        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.objects.all().delete()

        # Delete the bucket itself
        logger.info(
            "Sleeping 10 seconds for eventual consistency in deleting all bucker resources"
        )
        sleep(10)
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

    @staticmethod
    def parse_arn(arn: str) -> AwsArn:
        # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
        elements = arn.split(":", 5)
        result: AwsArn = {
            "arn": elements[0],
            "partition": elements[1],
            "service": elements[2],
            "region": elements[3],
            "account": elements[4],
            "resource": elements[5],
            "resource_type": None,
        }
        if "/" in result["resource"]:
            result["resource_type"], result["resource"] = result["resource"].split("/", 1)
        elif ":" in result["resource"]:
            result["resource_type"], result["resource"] = result["resource"].split(":", 1)
        return result


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
