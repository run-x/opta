from __future__ import annotations

from os import remove
from os.path import exists, getmtime
from time import sleep, time
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, TypedDict

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    # Only present when dev dependencies installed
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_eks import EKSClient
    from mypy_boto3_s3 import S3Client

import opta.constants as constants
from opta.constants import ONE_WEEK_UNIX
from opta.core.cloud_client import CloudClient
from opta.exceptions import MissingState, UserErrors
from opta.utils import fmt_msg, json, logger, yaml

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


class AWS(CloudClient):
    def __init__(self, layer: Optional["Layer"] = None):
        if layer:
            self.region = layer.root().providers["aws"]["region"]
        super().__init__(layer)

    def __get_dynamodb(self, dynamodb_table: str) -> DynamoDBClient:
        dynamodb_client: DynamoDBClient = boto3.client(
            "dynamodb", config=Config(region_name=self.region)
        )

        try:
            dynamodb_client.describe_table(TableName=dynamodb_table)
        except Exception:
            raise UserErrors(
                "Unable to reach Dynamo DB. Please check the configuration for the provided.\n"
                "Check if the Account ID or region are configured properly."
            )
        return dynamodb_client

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

        s3_client = boto3.client("s3", config=Config(region_name=self.region))
        return self._download_remote_blob(s3_client, bucket, config_path)

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3", config=Config(region_name=self.region))
        s3_client.put_object(
            Body=json.dumps(self.layer.structured_config()).encode("utf-8"),
            Bucket=bucket,
            Key=config_path,
        )
        logger.debug("Uploaded opta config to s3")

    def delete_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3", config=Config(region_name=self.region))
        resp = s3_client.delete_object(Bucket=bucket, Key=config_path)

        if resp["ResponseMetadata"]["HTTPStatusCode"] != 204:
            raise Exception(f"Failed to delete opta config in {bucket}/{config_path}.")

        for version in self.get_all_versions(bucket, config_path, self.region):
            s3_client.delete_object(Bucket=bucket, Key=config_path, VersionId=version)

        logger.info("Deleted opta config from s3")

    def delete_remote_state(self) -> None:
        bucket = self.layer.state_storage()
        providers = self.layer.gen_providers(0)
        dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]

        self.__get_dynamodb(dynamodb_table).delete_item(
            TableName=dynamodb_table,
            Key={"LockID": {"S": f"{bucket}/{self.layer.name}-md5"}},
        )

        s3_client = boto3.client("s3", config=Config(region_name=self.region))
        resp = s3_client.delete_object(Bucket=bucket, Key=self.layer.name)

        if resp["ResponseMetadata"]["HTTPStatusCode"] != 204:
            raise Exception(
                f"Failed to delete opta tf state in {bucket}/{self.layer.name}."
            )

        for version in self.get_all_versions(bucket, self.layer.name, self.region):
            s3_client.delete_object(Bucket=bucket, Key=self.layer.name, VersionId=version)
        logger.info(f"Deleted opta tf state for {self.layer.name}")

    def get_remote_state(self) -> str:
        bucket = self.layer.state_storage()
        s3_client = boto3.client("s3", config=Config(region_name=self.region))
        tf_state = self._download_remote_blob(s3_client, bucket, self.layer.name)
        if tf_state is None:
            raise MissingState("TF state does not exist.")
        return json.dumps(tf_state, indent=4)

    def get_terraform_lock_id(self) -> str:
        bucket = self.layer.state_storage()
        providers = self.layer.gen_providers(0)
        dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]

        tf_lock_data = self.__get_dynamodb(dynamodb_table).get_item(
            TableName=dynamodb_table,
            Key={"LockID": {"S": f"{bucket}/{self.layer.name}"}},
        )

        try:
            return json.loads(tf_lock_data["Item"]["Info"]["S"])["ID"]  # type: ignore
        except Exception:
            return ""

    def force_delete_terraform_lock_id(self) -> None:
        logger.info(
            "Trying to Remove the lock forcefully. Will try deleting Dynamo DB Entry."
        )
        bucket = self.layer.state_storage()
        providers = self.layer.gen_providers(0)
        dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]

        self.__get_dynamodb(dynamodb_table).delete_item(
            TableName=dynamodb_table,
            Key={"LockID": {"S": f"{bucket}/{self.layer.name}"}},
        )

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        prefix = "opta_config/"
        s3 = boto3.client("s3")
        remote_configs = {}
        for aws_bucket in self._get_opta_buckets():
            configs = {}
            response = s3.list_objects(Bucket=aws_bucket, Prefix=prefix, Delimiter="/")
            if "Contents" in response:
                for data in response["Contents"]:
                    structured_config = self._download_remote_blob(
                        s3, aws_bucket, data["Key"]
                    )
                    if structured_config:
                        configs[data["Key"][len(prefix) :]] = structured_config
                remote_configs[aws_bucket] = configs
        return remote_configs

    @staticmethod
    def _get_opta_buckets() -> List[str]:
        s3 = boto3.client("s3")
        aws_bucket = s3.list_buckets().get("Buckets", [])
        return [
            bucket["Name"]
            for bucket in aws_bucket
            if bucket["Name"].startswith("opta-tf-state")
        ]

    @staticmethod
    def get_all_versions(bucket: str, filename: str, region: str) -> List[str]:
        s3 = boto3.client("s3", config=Config(region_name=region))
        results = []
        for k in ["Versions", "DeleteMarkers"]:
            response = s3.list_object_versions(Bucket=bucket).get(k, [])  # type: ignore
            to_delete = [r["VersionId"] for r in response if r["Key"] == filename]  # type: ignore
            results.extend(to_delete)
        return results

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
    def prepare_dynamodb_write_tables_statements(dynamodb_table_arns: List[str]) -> dict:
        return {
            "Sid": "DynamodbWrite",
            "Action": [
                "dynamodb:BatchWriteItem",
                "dynamodb:DeleteItem",
                "dynamodb:PartiQLDelete",
                "dynamodb:PartiQLInsert",
                "dynamodb:PartiQLUpdate",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:ListTables",
                "dynamodb:BatchGetItem",
                "dynamodb:Describe*",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:PartiQLSelect",
            ],
            "Effect": "Allow",
            "Resource": [
                *[dynamodb_table_arn for dynamodb_table_arn in dynamodb_table_arns],
                *[
                    f"{dynamodb_table_arn}/index/*"
                    for dynamodb_table_arn in dynamodb_table_arns
                ],
            ],
        }

    @staticmethod
    def prepare_dynamodb_read_tables_statements(dynamodb_table_arns: List[str]) -> dict:
        return {
            "Sid": "DynamodbRead",
            "Action": [
                "dynamodb:ListTables",
                "dynamodb:BatchGetItem",
                "dynamodb:Describe*",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:PartiQLSelect",
            ],
            "Effect": "Allow",
            "Resource": [
                *[dynamodb_table_arn for dynamodb_table_arn in dynamodb_table_arns],
                *[
                    f"{dynamodb_table_arn}/index/*"
                    for dynamodb_table_arn in dynamodb_table_arns
                ],
            ],
        }

    @staticmethod
    def delete_bucket(bucket_name: str, region: str) -> None:
        # Before a bucket can be deleted, all of the objects inside must be removed.
        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.objects.all().delete()

        # Delete the bucket itself
        logger.info(
            "Sleeping 10 seconds for eventual consistency in deleting all bucket resources"
        )
        sleep(10)
        client = boto3.client("s3", config=Config(region_name=region))
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

    @staticmethod
    def bucket_exists(bucket_name: str, region: str) -> bool:
        s3 = boto3.client("s3", config=Config(region_name=region))
        try:
            s3.get_bucket_encryption(Bucket=bucket_name,)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return False
        return True

    @staticmethod
    def _download_remote_blob(
        s3_client: S3Client, bucket: str, key: str
    ) -> Optional["StructuredConfig"]:
        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read())
        except Exception:
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    def get_cluster_env(self) -> Tuple[str, str]:
        aws_provider = self.layer.root().providers["aws"]
        return aws_provider["region"], aws_provider["account_id"]

    def cluster_exist(self) -> bool:
        region, account_id = self.get_cluster_env()

        # Get the environment's account details from the opta config
        cluster_name = self.layer.get_cluster_name()
        client: EKSClient = boto3.client("eks", config=Config(region_name=region))

        try:
            client.describe_cluster(name=cluster_name)
            return True
        except client.exceptions.ResourceNotFoundException:
            return False

    def get_kube_context_name(self) -> str:
        region, account_id = self.get_cluster_env()
        # Get the environment's account details from the opta config
        cluster_name = self.layer.get_cluster_name()
        return f"{account_id}_{region}_{cluster_name}"

    def set_kube_config(self) -> None:
        kube_config_file_name = self.layer.get_kube_config_file_name()
        region, account_id = self.get_cluster_env()
        if exists(kube_config_file_name):
            if getmtime(kube_config_file_name) > time() - ONE_WEEK_UNIX:
                constants.GENERATED_KUBE_CONFIG = kube_config_file_name
                return
            else:
                remove(kube_config_file_name)

        # Get the environment's account details from the opta config
        cluster_name = self.layer.get_cluster_name()

        if not self.cluster_exist():
            raise Exception(
                "The EKS cluster name could not be determined -- please make sure it has been applied in the environment."
            )

        client: EKSClient = boto3.client("eks", config=Config(region_name=region))

        # get cluster details
        cluster = client.describe_cluster(name=cluster_name)
        cluster_cert = cluster["cluster"]["certificateAuthority"]["data"]
        cluster_ep = cluster["cluster"]["endpoint"]
        kube_context_name = self.get_kube_context_name()

        cluster_config = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "cluster": {
                        "server": str(cluster_ep),
                        "certificate-authority-data": str(cluster_cert),
                    },
                    "name": kube_context_name,
                }
            ],
            "contexts": [
                {
                    "context": {"cluster": kube_context_name, "user": kube_context_name},
                    "name": kube_context_name,
                }
            ],
            "current-context": kube_context_name,
            "preferences": {},
            "users": [
                {
                    "name": kube_context_name,
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1beta1",
                            "command": "aws",
                            "args": [
                                "--region",
                                region,
                                "eks",
                                "get-token",
                                "--cluster-name",
                                cluster_name,
                            ],
                            "env": None,
                        }
                    },
                }
            ],
        }
        with open(kube_config_file_name, "w") as f:
            yaml.dump(cluster_config, f)
        constants.GENERATED_KUBE_CONFIG = kube_config_file_name
        return


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
