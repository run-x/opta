from botocore.exceptions import ClientError
from pytest_mock import MockFixture

from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import fmt_msg
from tests.utils import MockedCmdOut


class TestTerraform:
    def test_init(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.nice_run")

        # Calling terraform apply should also call terraform init
        tf_init = mocker.patch("opta.core.terraform.Terraform.init")
        fake_layer = mocker.Mock(spec=Layer)
        Terraform.apply(fake_layer)
        assert tf_init.call_count == 1

        # Calling terraform plan should also call terraform init
        Terraform.plan()
        assert tf_init.call_count == 2

    def test_get_modules(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.Terraform.download_state", return_value=True)

        tf_state_list_output = fmt_msg(
            """
            ~data.aws_caller_identity.provider
            ~data.aws_eks_cluster_auth.k8s
            ~module.redis.data.aws_security_group.security_group[0]
            ~module.redis.aws_elasticache_replication_group.redis_cluster
            ~module.doc_db.data.aws_security_group.security_group[0]
        """
        )

        mocker.patch(
            "opta.core.terraform.nice_run",
            return_value=MockedCmdOut(tf_state_list_output),
        )
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.name = "blah"
        assert {"redis", "doc_db"} == Terraform.get_existing_modules(mocked_layer)

    def test_rollback(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.nice_run")

        # Mock existing terraform resources
        mocker.patch(
            "opta.core.terraform.Terraform.get_existing_resources",
            return_value=["fake.tf.resource.address.1"],
        )

        # Mock existing AWS resources
        # Note that `fake.tf.resource.address.2` is a stale resource that is
        # not in the terraform state.
        mocked_aws_class = mocker.patch("opta.core.terraform.AWS")
        mocked_aws_instance = mocked_aws_class.return_value
        mocked_aws_instance.get_opta_resources.return_value = {
            "fake.tf.resource.address.1": "fake:aws:us-east-1:resource:arn:i-1",
            "fake.tf.resource.address.2": "fake:aws:us-east-1:resource:arn:i-2",
        }

        mocked_import = mocker.patch("opta.core.terraform.Terraform.import_resource")
        mocked_destroy = mocker.patch("opta.core.terraform.Terraform.destroy")

        # Run rollback
        fake_layer = mocker.Mock(spec=Layer)
        Terraform.rollback(fake_layer)

        # The stale resource should be imported and destroyed.
        mocked_import.assert_called_once_with("fake.tf.resource.address.2", "i-2")
        mocked_destroy.assert_called_once_with("-target=fake.tf.resource.address.2")

        # Test rollback again, but without the stale resource.
        del mocked_aws_instance.get_opta_resources.return_value[
            "fake.tf.resource.address.2"
        ]

        mocked_import = mocker.patch("opta.core.terraform.Terraform.import_resource")
        mocked_destroy = mocker.patch("opta.core.terraform.Terraform.destroy")

        # Run rollback
        Terraform.rollback(mocker.Mock(spec=Layer))

        # Import and destroy should *not* be called.
        assert not mocked_import.called
        assert not mocked_destroy.called

    def test_download_state(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "s3": {
                        "bucket": "opta-tf-state-test-dev1",
                        "key": "dev1",
                        "dynamodb_table": "opta-tf-state-test-dev1",
                        "region": "us-east-1",
                    }
                }
            }
        }
        layer.name = "blah"
        patched_init = mocker.patch(
            "opta.core.terraform.Terraform.init", return_value=True
        )
        mocked_s3_client = mocker.Mock()
        mocked_boto_client = mocker.patch(
            "opta.core.terraform.boto3.client", return_value=mocked_s3_client
        )

        assert Terraform.download_state(layer)
        layer.gen_providers.assert_called_once_with(0)
        mocked_s3_client.download_file.assert_called_once_with(
            "opta-tf-state-test-dev1", "dev1", "./terraform.tfstate"
        )
        patched_init.assert_not_called()
        mocked_boto_client.assert_called_once_with("s3")

    def test_create_state_storage(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "s3": {
                        "bucket": "opta-tf-state-test-dev1",
                        "key": "dev1",
                        "dynamodb_table": "opta-tf-state-test-dev1",
                        "region": "us-east-1",
                    }
                }
            }
        }
        mocked_s3_client = mocker.Mock()
        mocked_dynamodb_client = mocker.Mock()
        mocked_iam_client = mocker.Mock()
        mocked_boto3 = mocker.patch("opta.core.terraform.boto3")
        mocked_boto3.client.side_effect = [
            mocked_s3_client,
            mocked_dynamodb_client,
            mocked_iam_client,
        ]

        mocked_s3_client.get_bucket_encryption.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchBucket", "Message": "Blah"}},
            operation_name="Blah",
        )

        mocked_dynamodb_client.describe_table.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ResourceNotFoundException", "Message": "Blah"}
            },
            operation_name="Blah",
        )

        Terraform.create_state_storage(layer)

        layer.gen_providers.assert_called_once_with(0)
        mocked_dynamodb_client.create_table.assert_called_once_with(
            TableName="opta-tf-state-test-dev1",
            KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "LockID", "AttributeType": "S"}],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 20, "WriteCapacityUnits": 20},
        )
        mocked_s3_client.create_bucket.assert_called_once_with(
            Bucket="opta-tf-state-test-dev1"
        )
        mocked_s3_client.put_bucket_encryption.assert_called_once_with(
            Bucket="opta-tf-state-test-dev1",
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}},
                ]
            },
        )
        mocked_s3_client.put_public_access_block.assert_called_once_with(
            Bucket="opta-tf-state-test-dev1",
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        mocked_boto3.client.assert_has_calls(
            [
                mocker.call("s3"),
                mocker.call("dynamodb", config=mocker.ANY),
                mocker.call("iam", config=mocker.ANY),
            ]
        )
