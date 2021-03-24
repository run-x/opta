from botocore.exceptions import ClientError
from pytest_mock import MockFixture

from opta.core.terraform import Terraform, fetch_terraform_state_resources
from opta.layer import Layer
from opta.module import Module
from tests.utils import get_call_args


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

        mocker.patch(
            "opta.core.terraform.Terraform.get_state",
            return_value={
                "resources": [
                    {
                        "module": "module.redis",
                        "mode": "managed",
                        "type": "aws_elasticache_replication_group",
                        "name": "redis_cluster",
                    },
                    {
                        "module": "module.redis",
                        "mode": "data",
                        "type": "aws_eks_cluster_auth",
                        "name": "k8s",
                    },
                    {
                        "module": "module.redis",
                        "mode": "managed",
                        "type": "aws_elasticache_replication_group",
                        "name": "redis_cluster",
                    },
                    {
                        "module": "module.doc_db",
                        "mode": "data",
                        "type": "aws_security_group",
                        "name": "security_group",
                    },
                    {"mode": "data", "type": "aws_caller_identity", "name": "provider"},
                    {"mode": "data", "type": "aws_eks_cluster_auth", "name": "k8s"},
                ]
            },
        )
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.name = "blah"
        assert {"redis", "doc_db"} == Terraform.get_existing_modules(mocked_layer)

    def test_rollback(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.nice_run")

        # Mock existing terraform resources
        mocker.patch(
            "opta.core.terraform.Terraform.get_existing_module_resources",
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
        mocked_destroy = mocker.patch("opta.core.terraform.Terraform.destroy_resources")

        # Run rollback
        fake_layer = mocker.Mock(spec=Layer)
        Terraform.rollback(fake_layer)

        # The stale resource should be imported and destroyed.
        mocked_import.assert_called_once_with("fake.tf.resource.address.2", "i-2")
        mocked_destroy.assert_called_once_with(fake_layer, ["fake.tf.resource.address.2"])

        # Test rollback again, but without the stale resource.
        del mocked_aws_instance.get_opta_resources.return_value[
            "fake.tf.resource.address.2"
        ]

        mocked_import = mocker.patch("opta.core.terraform.Terraform.import_resource")
        mocked_destroy = mocker.patch("opta.core.terraform.Terraform.destroy_resources")

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

    def test_destroy_modules_in_order(self, mocker: MockFixture) -> None:
        fake_modules = [mocker.Mock(spec=Module) for _ in range(3)]
        for i, module in enumerate(fake_modules):
            module.name = f"fake_module_{i}"
            module.get_terraform_resources = lambda: []

        fake_layer = mocker.Mock(spec=Layer)
        fake_layer.modules = fake_modules

        mocker.patch("opta.core.terraform.Terraform.refresh")
        mocked_cmd = mocker.patch("opta.core.terraform.nice_run")
        Terraform.destroy_all(fake_layer)
        assert get_call_args(mocked_cmd) == [
            ["terraform", "destroy", "-target=module.fake_module_2"],
            ["terraform", "destroy", "-target=module.fake_module_1"],
            ["terraform", "destroy", "-target=module.fake_module_0"],
        ]

        # Additionally verify this works for destroy_resources()
        fake_resources = [
            "module.fake_module_1.test_resource.bar",
            "module.fake_module_2.test_resource.foo",
            "module.fake_module_0.test_resource.baz",
        ]
        mocked_cmd = mocker.patch("opta.core.terraform.nice_run")
        mocked_destroy_hz = mocker.patch(
            "opta.core.terraform.Terraform.destroy_hosted_zone_resources"
        )
        Terraform.destroy_resources(fake_layer, fake_resources)
        assert get_call_args(mocked_cmd) == [
            ["terraform", "destroy", "-target=module.fake_module_2.test_resource.foo"],
            ["terraform", "destroy", "-target=module.fake_module_1.test_resource.bar"],
            ["terraform", "destroy", "-target=module.fake_module_0.test_resource.baz"],
        ]
        # The hosted zone should not be destroyed since it was not in the specified resources.
        assert mocked_destroy_hz.call_count == 0

        # Now the hosted zone shoud be destroyed.
        fake_resources.append("module.fake_module_1.aws_route53_zone.public")
        Terraform.destroy_resources(fake_layer, fake_resources)
        assert mocked_destroy_hz.call_count == 1

    def test_fetch_terraform_state_resources(self, mocker: MockFixture) -> None:
        raw_s3_tf_state = {
            "resources": [
                {
                    "module": "module.testmodule",
                    "type": "test_resource",
                    "name": "test",
                    "instances": [{"attributes": {"test_value": "foobar"}}],
                }
            ]
        }
        mocker.patch("opta.core.terraform.Terraform.download_state")
        mocker.patch(
            "opta.core.terraform.Terraform.get_state", return_value=raw_s3_tf_state
        )

        fake_layer = mocker.Mock(spec=Layer)
        parsed_tf_state = fetch_terraform_state_resources(fake_layer)

        assert parsed_tf_state == {
            "module.testmodule.test_resource.test": {
                "module": "module.testmodule",
                "name": "test",
                "test_value": "foobar",
                "type": "test_resource",
            }
        }
