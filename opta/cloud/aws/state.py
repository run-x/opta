# new-module-api

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any, Dict, cast

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_s3.literals import BucketLocationConstraintType

from opta.core.terraform2.state import StateNotFoundError, StateStore, StoreConfig
from opta.core.terraform2.terraform_file import TerraformFile
from opta.exceptions import UserErrors
from opta.utils import logger

from . import _client


class S3Store(StateStore):
    def configure_storage(self) -> None:
        self._configure_bucket()
        self._configure_dynamodb_table()
        self._configure_iam()

    def configure_terraform_file(self, tf: TerraformFile) -> None:
        tf.add_backend(
            "s3",
            {
                "bucket": self._bucket,
                "key": self.config.layer_name,
                "dynamodb_table": self._bucket,
                "region": self._region,
            },
        )

    def is_storage_configured(self) -> bool:
        # TODO: Also check for the dynamodb table and iam present
        s3 = _client.s3(self._region)
        try:
            s3.get_bucket_encryption(Bucket=self._bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return False
            raise e
        return True

    def read_raw(self) -> str:
        bucket = self._bucket
        region = self._region
        key = self._object_key
        logger.debug(
            f"Found an s3 backend in bucket {bucket} and key {key}, "
            "gonna try to download the statefile from there"
        )

        s3 = _client.s3(region)

        f = io.StringIO()
        try:
            s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=f)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.debug("Did not find terraform state file")
                raise StateNotFoundError()

            raise

        contents = f.getvalue()

        return contents

    @property
    def _bucket(self) -> str:
        c = self.config

        # TODO: Handle bucket suffixes, along with handling existing buckets without the suffix
        return f"opta-tf-state-{c.org_name}-{c.layer_name}"

    def _configure_bucket(self) -> None:
        bucket_name = self._bucket
        region = self._region

        s3 = _client.s3(region)

        try:
            s3.get_bucket_encryption(Bucket=bucket_name)
            return
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AuthFailure":
                raise UserErrors(
                    "The AWS Credentials are not configured properly.\n"
                    "Visit https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html "
                    "for more information."
                )

            if error_code == "AccessDenied":
                raise UserErrors(
                    f"We were unable to access the S3 bucket, {bucket_name} on your AWS account (opta needs this to store state).\n"
                    "Possible Issues: \n"
                    " - Bucket name is not unique and might be present in some other Account. Try updating the name in Configuration file to something else.\n"
                    " - It could also mean that your AWS account has insufficient permissions.\n"
                    "Please fix these issues and try again!"
                )

            if error_code != "NoSuchBucket":
                error_message = e.response["Error"]["Message"]
                raise UserErrors(
                    "When trying to determine the status of the state bucket, we got an "
                    f"{error_code} error with the message {error_message}"
                )

        logger.debug("S3 bucket for terraform state not found, creating a new one")

        create_kwargs: Dict[str, Any] = {}
        if region != "us-east-1":
            # S3 API doesn't allow specifying us-east-1 as a location constraint, so we need to handle this
            # special case. When the constraint is not given, the bucket is created in us-east-1
            if TYPE_CHECKING:
                region = cast(BucketLocationConstraintType, region)

            create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

        s3.create_bucket(Bucket=bucket_name, **create_kwargs)

        waiter = s3.get_waiter("bucket_exists")
        waiter.wait(Bucket=bucket_name, WaiterConfig={"Delay": 5, "MaxAttempts": 10})

        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}},
                ]
            },
        )

        # Visit (https://run-x.atlassian.net/browse/RUNX-1125) for further reference
        s3.put_bucket_versioning(
            Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"},
        )
        s3.put_bucket_lifecycle(
            Bucket=bucket_name,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "ID": "default",
                        "Prefix": "/",
                        "Status": "Enabled",
                        "NoncurrentVersionTransition": {
                            "NoncurrentDays": 30,
                            "StorageClass": "GLACIER",
                        },
                        "NoncurrentVersionExpiration": {"NoncurrentDays": 60},
                        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 10},
                    },
                ]
            },
        )

    def _configure_dynamodb_table(self) -> None:
        region = self._region
        dynamodb_table = self._bucket

        dynamodb = _client.dynamodb(region)

        try:
            dynamodb.describe_table(TableName=dynamodb_table)
            return
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "ResourceNotFoundException":
                error_message = e.response["Error"]["Message"]
                raise UserErrors(
                    "When trying to determine the status of the state dynamodb table, we got an "
                    f"{error_code} error with the message {error_message}"
                )

        logger.debug("Dynamodb table for terraform state not found, creating a new one")

        dynamodb.create_table(
            TableName=dynamodb_table,
            KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "LockID", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def _configure_iam(self) -> None:
        iam = _client.iam()
        try:
            iam.create_service_linked_role(AWSServiceName="autoscaling.amazonaws.com",)
        except ClientError as e:
            if e.response["Error"]["Code"] != "InvalidInput":
                raise UserErrors(
                    "When trying to create the aws service linked role for autoscaling, we got an "
                    f"{e.response['Error']['Code']} error with the message "
                    f"{e.response['Error']['Message']}"
                )
            logger.debug("Autoscaling service linked role present")

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
            logger.debug("Load balancing service linked role present")

    @property
    def _object_key(self) -> str:
        return self.config.layer_name

    @property
    def _region(self) -> str:
        region = self.config.region
        if region is None:  # Checked by _validate_config
            raise AssertionError("Unexpected region=None")

        return region

    @classmethod
    def _validate_config(cls, config: StoreConfig) -> None:
        if config.region is None:
            raise ValueError(f"region must be configured for {cls.__name__}")
