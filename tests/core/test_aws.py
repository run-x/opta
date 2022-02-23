from unittest.mock import Mock

from botocore.response import StreamingBody
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3 import S3Client
from pytest import fixture
from pytest_mock import MockFixture

from opta.core.aws import AWS
from opta.layer import Layer


class TestAWS:
    @fixture
    def aws_layer(self) -> Mock:
        layer = Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "aws"
        layer.name = "mock_name"
        layer.org_name = "mock_org_name"
        layer.providers = {"aws": {"region": "us-east-1", "account_id": "111111111111"}}

        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "s3": {
                        "bucket": f"opta-tf-state-{layer.org_name}-{layer.name}",
                        "key": "mock_key",
                        "dynamodb_table": f"opta-tf-state-{layer.org_name}-{layer.name}",
                        "region": "us-east-1",
                    }
                }
            },
            "provider": {"aws": {"region": "us-east-1", "account_id": "111111111111"}},
        }

        return layer

    def test_get_terraform_lock_id(self, mocker: MockFixture, aws_layer: Mock) -> None:
        mock_dynamodb_client_instance = mocker.Mock(spec=DynamoDBClient)
        mocker.patch(
            "opta.core.aws.boto3.client", return_value=mock_dynamodb_client_instance
        )

        mock_dynamodb_client_instance.get_item.return_value = {
            "Item": {"Info": {"S": '{"ID": "mock_lock_id"}'}}
        }

        mock_aws = AWS(aws_layer)
        assert mock_aws.get_terraform_lock_id() == "mock_lock_id"

        mock_dynamodb_client_instance.get_item.assert_called_once_with(
            TableName=aws_layer.gen_providers(0)["terraform"]["backend"]["s3"][
                "dynamodb_table"
            ],
            Key={"LockID": {"S": f"{aws_layer.state_storage()}/{aws_layer.name}"}},
        )

    def test_force_delete_terraform_lock_id(
        self, mocker: MockFixture, aws_layer: Mock
    ) -> None:
        mock_dynamodb_client_instance = mocker.Mock(spec=DynamoDBClient)
        mocker.patch(
            "opta.core.aws.boto3.client", return_value=mock_dynamodb_client_instance
        )
        mock_aws = AWS(aws_layer)
        mock_aws.force_delete_terraform_lock_id()
        mock_dynamodb_client_instance.delete_item.assert_called_once_with(
            TableName=aws_layer.gen_providers(0)["terraform"]["backend"]["s3"][
                "dynamodb_table"
            ],
            Key={"LockID": {"S": f"{aws_layer.state_storage()}/{aws_layer.name}"}},
        )

    def test_get_detailed_config_map_configuration_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS.get_bucket_list", return_value=["test"])
        mock_s3_client_instance.list_objects.return_value = {
            "Contents": [{"Key": "opta_config/test-config"}]
        }
        mock_stream = mocker.Mock(spec=StreamingBody)
        mock_stream.read.return_value = """{"original_spec": "actual_config"}"""
        mock_s3_client_instance.get_object.return_value = {"Body": mock_stream}
        AWS.get_detailed_config_map()
        mock_s3_client_instance.list_objects.assert_called_once_with(
            Bucket="test", Prefix="opta_config/", Delimiter="/"
        )
        mock_s3_client_instance.get_object.assert_called_once_with(
            Bucket="test", Key="opta_config/test-config"
        )

    def test_get_detailed_config_map_configuration_not_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS.get_bucket_list", return_value=["test"])
        mock_s3_client_instance.list_objects.return_value = {}
        AWS.get_detailed_config_map()
        mock_s3_client_instance.list_objects.assert_called_once_with(
            Bucket="test", Prefix="opta_config/", Delimiter="/"
        )
        mock_s3_client_instance.get_object.assert_not_called()

    def test_get_detailed_config_map_buckets_not_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS.get_bucket_list", return_value=[])
        mock_s3_client_instance.list_objects.return_value = {}
        AWS.get_detailed_config_map()
        mock_s3_client_instance.list_objects.assert_not_called()
        mock_s3_client_instance.get_object.assert_not_called()
