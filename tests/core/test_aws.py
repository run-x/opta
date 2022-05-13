from datetime import datetime
from unittest.mock import Mock

import pytest
from botocore.response import StreamingBody
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3 import S3Client
from pytest import fixture
from pytest_mock import MockFixture

from opta.constants import GENERATED_KUBE_CONFIG_DIR
from opta.core.aws import AWS
from opta.exceptions import MissingState
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
        layer.get_cluster_name.return_value = "mocked_cluster_name"
        layer.get_kube_config_file_name.return_value = f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{layer.root().name}-{layer.cloud}.yaml"

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

    def test_aws_set_kube_config(self, mocker: MockFixture, aws_layer: Mock) -> None:
        mocked_exist = mocker.patch("opta.core.aws.exists")
        mocked_exist.return_value = False
        mock_eks_client = mocker.Mock()
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_eks_client)
        mock_eks_client.describe_cluster.return_value = {
            "cluster": {
                "certificateAuthority": {"data": "ca-data"},
                "endpoint": "eks-endpoint",
            }
        }

        mocker.patch(
            "opta.core.aws.AWS.cluster_exist", return_value=True,
        )
        mocked_file = mocker.patch("opta.core.aws.open", mocker.mock_open(read_data=""))
        AWS(aws_layer).set_kube_config()
        config_file_name = f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{aws_layer.root().name}-{aws_layer.cloud}.yaml"
        mocked_file.assert_called_once_with(config_file_name, "w")
        mocked_file().write.assert_called_once_with(
            "apiVersion: v1\n"
            "clusters:\n"
            "- cluster: {certificate-authority-data: ca-data, server: eks-endpoint}\n"
            "  name: 111111111111_us-east-1_mocked_cluster_name\n"
            "contexts:\n"
            "- context: {cluster: 111111111111_us-east-1_mocked_cluster_name, user: "
            "111111111111_us-east-1_mocked_cluster_name}\n"
            "  name: 111111111111_us-east-1_mocked_cluster_name\n"
            "current-context: 111111111111_us-east-1_mocked_cluster_name\n"
            "kind: Config\n"
            "preferences: {}\n"
            "users:\n"
            "- name: 111111111111_us-east-1_mocked_cluster_name\n"
            "  user:\n"
            "    exec:\n"
            "      apiVersion: client.authentication.k8s.io/v1beta1\n"
            "      args: [--region, us-east-1, eks, get-token, --cluster-name, "
            "mocked_cluster_name]\n"
            "      command: aws\n"
            "      env: null\n"
        )

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

    def test_get_all_remote_configs_configuration_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS._get_opta_buckets", return_value=["test"])
        mock_s3_client_instance.list_objects.return_value = {
            "Contents": [{"Key": "opta_config/test-config"}]
        }
        mock_stream = mocker.Mock(spec=StreamingBody)
        mock_stream.read.return_value = """{"original_spec": "actual_config"}"""
        mock_s3_client_instance.get_object.return_value = {"Body": mock_stream}
        mock_download_remote_blob = mocker.patch(
            "opta.core.aws.AWS._download_remote_blob",
            return_value={
                "opta_version": "dev",
                "date": datetime.utcnow().isoformat(),
                "original_spec": "actual_config",
                "defaults": {},
            },
        )

        AWS().get_all_remote_configs()
        mock_s3_client_instance.list_objects.assert_called_once_with(
            Bucket="test", Prefix="opta_config/", Delimiter="/"
        )
        mock_download_remote_blob.assert_called_once_with(
            mock_s3_client_instance, "test", "opta_config/test-config"
        )

    def test_get_all_remote_configs_configuration_not_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS._get_opta_buckets", return_value=["test"])
        mock_s3_client_instance.list_objects.return_value = {}
        mock_download_remote_blob = mocker.patch(
            "opta.core.aws.AWS._download_remote_blob"
        )
        AWS().get_all_remote_configs()
        mock_s3_client_instance.list_objects.assert_called_once_with(
            Bucket="test", Prefix="opta_config/", Delimiter="/"
        )
        mock_download_remote_blob.assert_not_called()

    def test_get_all_remote_configs_buckets_not_present(
        self, mocker: MockFixture
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mocker.patch("opta.core.aws.AWS._get_opta_buckets", return_value=[])
        mock_s3_client_instance.list_objects.return_value = {}
        mock_download_remote_blob = mocker.patch(
            "opta.core.aws.AWS._download_remote_blob"
        )
        AWS().get_all_remote_configs()
        mock_s3_client_instance.list_objects.assert_not_called()
        mock_download_remote_blob.assert_not_called()

    def test_get_remote_state(self, mocker: MockFixture, aws_layer: Mock) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mock_download_remote_blob = mocker.patch(
            "opta.core.aws.AWS._download_remote_blob", return_value="""{"test": "test"}"""
        )
        AWS(layer=aws_layer).get_remote_state()
        mock_download_remote_blob.assert_called_once_with(
            mock_s3_client_instance, aws_layer.state_storage(), aws_layer.name
        )

    def test_get_remote_state_state_does_not_exist(
        self, mocker: MockFixture, aws_layer: Mock
    ) -> None:
        mock_s3_client_instance = mocker.Mock(spec=S3Client)
        mocker.patch("opta.core.aws.boto3.client", return_value=mock_s3_client_instance)
        mock_download_remote_blob = mocker.patch(
            "opta.core.aws.AWS._download_remote_blob", return_value=None
        )
        with pytest.raises(MissingState):
            AWS(layer=aws_layer).get_remote_state()
        mock_download_remote_blob.assert_called_once_with(
            mock_s3_client_instance, aws_layer.state_storage(), aws_layer.name
        )
