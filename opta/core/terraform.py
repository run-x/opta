import json
from typing import TYPE_CHECKING, List, Set

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import deep_merge, logger

if TYPE_CHECKING:
    from opta.layer import Layer


class Terraform:
    # True if terraform.tfstate is downloaded.
    downloaded_state = False

    @classmethod
    def init(cls) -> None:
        nice_run(["terraform", "init"], check=True)

    # Get outputs of the current terraform state
    @classmethod
    def get_outputs(cls) -> dict:
        raw_output = nice_run(
            ["terraform", "output", "-json"], check=True, capture_output=True
        ).stdout.decode("utf-8")
        outputs = json.loads(raw_output)
        cleaned_outputs = {}
        for k, v in outputs.items():
            cleaned_outputs[k] = v.get("value")
        return cleaned_outputs

    # Get the full terraform state.
    @classmethod
    def get_state(cls) -> dict:
        raw_state = nice_run(
            ["terraform", "show", "-json"], check=True, capture_output=True
        ).stdout.decode("utf-8")
        return json.loads(raw_state)

    @classmethod
    def apply(cls, *tf_flags: List[str]) -> None:
        cls.init()
        nice_run(["terraform", "apply", *tf_flags], check=True)

    @classmethod
    def plan(cls, *tf_flags: List[str]) -> None:
        cls.init()
        nice_run(["terraform", "plan", *tf_flags], check=True)

    @classmethod
    def get_existing_modules(cls, layer: "Layer") -> Set[str]:
        existing_resources = cls.get_existing_resources(layer)
        module_resources = [r for r in existing_resources if r.startswith("module")]
        return set(map(lambda r: r.split(".")[1], module_resources))

    @classmethod
    def get_existing_resources(cls, layer: "Layer") -> List[str]:
        if not cls.downloaded_state:
            success = cls.download_state(layer)
            if not success:
                logger.info(
                    "Could not fetch remote terraform state, assuming no resources exist yet."
                )
                return []

        return (
            nice_run(["terraform", "state", "list"], check=True, capture_output=True)
            .stdout.decode("utf-8")
            .split("\n")
        )

    @classmethod
    def download_state(cls, layer: "Layer") -> bool:
        cls.init()

        providers = layer.gen_providers(0)
        if "s3" in providers.get("terraform", {}).get("backend", {}):
            bucket = providers["terraform"]["backend"]["s3"]["bucket"]
            key = providers["terraform"]["backend"]["s3"]["key"]
            logger.debug(
                f"Found an s3 backend in bucket {bucket} and key {key}, "
                "gonna try to download the statefile from there"
            )
            s3 = boto3.client("s3")
            try:
                s3.download_file(bucket, key, "./terraform.tfstate")
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    # The object does not exist.
                    return False
                raise

        cls.downloaded_state = True
        return True

    @classmethod
    def create_state_storage(cls, layer: "Layer") -> None:
        """
        Idempotently create remote storage for tf state
        """
        providers = layer.gen_providers(0)
        if "s3" in providers.get("terraform", {}).get("backend", {}):
            bucket_name = providers["terraform"]["backend"]["s3"]["bucket"]
            dynamodb_table = providers["terraform"]["backend"]["s3"]["dynamodb_table"]
            region = providers["terraform"]["backend"]["s3"]["region"]
            s3 = boto3.client("s3")
            dynamodb = boto3.client("dynamodb", config=Config(region_name=region))
            iam = boto3.client("iam", config=Config(region_name=region))
            try:
                s3.get_bucket_encryption(Bucket=bucket_name,)
            except ClientError as e:
                if e.response["Error"]["Code"] == "AccessDenied":
                    raise UserErrors(
                        f"The AWS S3 bucket, {bucket_name} we were trying to access "
                        "cause it'd hold the state could not be reached cause our access"
                        "was denied. This means that either the creds you're running with "
                        "aren't giving you the read+write permissions or that this bucket "
                        "already exists and this AWS account doesn't own it."
                    )
                if e.response["Error"]["Code"] != "NoSuchBucket":
                    raise UserErrors(
                        "When trying to determine the status of the state bucket, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                logger.info("S3 bucket for terraform state not found, creating a new one")
                if region == "us-east-1":
                    s3.create_bucket(Bucket=bucket_name,)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )
                s3.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "AES256"
                                },
                            },
                        ]
                    },
                )
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )

            try:
                dynamodb.describe_table(TableName=dynamodb_table)
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise UserErrors(
                        "When trying to determine the status of the state dynamodb table, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Dynamodb table for terraform state not found, creating a new one")
                dynamodb.create_table(
                    TableName=dynamodb_table,
                    KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
                    AttributeDefinitions=[
                        {"AttributeName": "LockID", "AttributeType": "S"},
                    ],
                    BillingMode="PROVISIONED",
                    ProvisionedThroughput={
                        "ReadCapacityUnits": 20,
                        "WriteCapacityUnits": 20,
                    },
                )
            # Create the service linked roles
            try:
                iam.create_service_linked_role(
                    AWSServiceName="autoscaling.amazonaws.com",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "InvalidInput":
                    raise UserErrors(
                        "When trying to create the aws service linked role for autoscaling, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Autoscaling service linked role present")
            try:
                iam.create_service_linked_role(
                    AWSServiceName="elasticloadbalancing.amazonaws.com",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "InvalidInput":
                    raise UserErrors(
                        "When trying to create the aws service linked role for load balancing, we got an "
                        f"{e.response['Error']['Code']} error with the message "
                        f"{e.response['Error']['Message']}"
                    )
                print("Load balancing service linked role present")


def get_terraform_outputs() -> dict:
    """ Fetch terraform outputs from existing TF file """
    Terraform.init()
    current_outputs = Terraform.get_outputs()
    parent_outputs = _fetch_parent_outputs()
    return deep_merge(current_outputs, parent_outputs)


def _fetch_parent_outputs() -> dict:
    # Fetch the terraform state
    state = Terraform.get_state()

    # Fetch any parent remote states
    root_module = state.get("values", {}).get("root_module", {})
    resources = root_module.get("resources", [])
    parent_states = [
        resource
        for resource in resources
        if resource.get("type") == "terraform_remote_state"
    ]

    # Grab all outputs from each remote state and save it.
    parent_state_outputs = {}
    for parent in parent_states:
        parent_outputs = parent.get("values", {}).get("outputs", {})
        for k, v in parent_outputs.items():
            parent_name = parent.get("name")
            output_name = f"{parent_name}.{k}"
            parent_state_outputs[output_name] = v

    return parent_state_outputs
