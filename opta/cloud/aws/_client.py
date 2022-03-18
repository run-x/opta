from __future__ import annotations

from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_s3 import S3Client


def dynamodb(region: str) -> DynamoDBClient:
    return boto3.client("dynamodb", config=_config(region))


def iam() -> Any:
    return boto3.client("iam")


def s3(region: str) -> S3Client:
    return boto3.client("s3", config=_config(region))


def _config(region: str) -> Config:
    return Config(region_name=region)
