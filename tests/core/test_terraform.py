from botocore.exceptions import ClientError
from google.api_core.exceptions import ClientError as GoogleClientError
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

    def test_aws_download_state(self, mocker: MockFixture) -> None:
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
        layer.cloud = "aws"
        mocker.patch(
            "opta.core.terraform.Terraform._aws_verify_storage", return_value=True
        )
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

    def test_google_download_state(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "gcs": {"bucket": "opta-tf-state-test-dev1", "prefix": "dev1"}
                }
            },
            "provider": {"google": {"region": "us-central1", "project": "dummy-project"}},
        }
        layer.name = "blah"
        layer.cloud = "google"
        mocker.patch(
            "opta.core.terraform.Terraform._gcp_verify_storage", return_value=True
        )
        patched_init = mocker.patch(
            "opta.core.terraform.Terraform.init", return_value=True
        )
        mocked_credentials = mocker.Mock()
        mocked_gcp_credentials = mocker.patch(
            "opta.core.terraform.GCP.get_credentials",
            return_value=[mocked_credentials, "dummy-project"],
        )
        mocked_storage_client = mocker.Mock()
        mocked_client_constructor = mocker.patch(
            "opta.core.terraform.storage.Client", return_value=mocked_storage_client
        )
        mocked_bucket_object = mocker.Mock()
        mocked_storage_client.get_bucket.return_value = mocked_bucket_object
        read_data = ""
        mocked_file = mocker.mock_open(read_data=read_data)
        mocked_open = mocker.patch("opta.core.terraform.open", mocked_file)

        assert Terraform.download_state(layer)

        patched_init.assert_not_called()
        mocked_gcp_credentials.assert_called_once_with()
        mocked_client_constructor.assert_called_once_with(
            project="dummy-project", credentials=mocked_credentials
        )
        mocked_storage_client.get_bucket.assert_called_once_with(
            "opta-tf-state-test-dev1"
        )
        mocked_open.assert_called_once_with("./terraform.tfstate", "wb")
        mocked_storage_client.download_blob_to_file.assert_called_once_with(
            mocker.ANY, mocker.ANY
        )

    def test_create_aws_state_storage(self, mocker: MockFixture) -> None:
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

    def test_create_google_state_storage(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "gcs": {"bucket": "opta-tf-state-test-dev1", "prefix": "dev1"}
                }
            },
            "provider": {"google": {"region": "us-central1", "project": "dummy-project"}},
        }
        mocked_gcp = mocker.patch("opta.core.terraform.GCP")
        mocked_credentials = mocker.Mock()
        mocked_gcp.get_credentials.return_value = tuple(
            [mocked_credentials, "dummy-project"]
        )
        mocked_storage = mocker.patch("opta.core.terraform.storage")
        mocked_storage_client = mocker.Mock()
        mocked_storage.Client.return_value = mocked_storage_client
        get_bucket_error = GoogleClientError(message="blah")
        get_bucket_error.code = 404
        mocked_storage_client.get_bucket.side_effect = get_bucket_error

        mocked_google_credentials = mocker.patch("opta.core.terraform.GoogleCredentials")
        mocked_api_credentials = mocker.Mock()
        mocked_google_credentials.get_application_default.return_value = (
            mocked_api_credentials
        )
        mocked_discovery = mocker.patch("opta.core.terraform.discovery")
        mocked_service = mocker.Mock()
        mocked_discovery.build.return_value = mocked_service
        mocked_service_services = mocker.Mock()
        mocked_service.services.return_value = mocked_service_services
        mocked_request = mocker.Mock()
        mocked_service_services.enable.return_value = mocked_request
        mocked_response: dict = {}
        mocked_request.execute.return_value = mocked_response
        mocked_sleep = mocker.patch("opta.core.terraform.time.sleep")

        Terraform.create_state_storage(layer)
        mocked_gcp.get_credentials.assert_called_once_with()
        mocked_storage.Client.assert_called_once_with(
            project="dummy-project", credentials=mocked_credentials
        )
        mocked_storage_client.get_bucket.assert_called_once_with(
            "opta-tf-state-test-dev1"
        )
        mocked_storage_client.create_bucket.assert_called_once_with(
            "opta-tf-state-test-dev1", location="us-central1"
        )
        mocked_google_credentials.get_application_default.assert_called_once_with()
        mocked_discovery.build.assert_called_once_with(
            "serviceusage",
            "v1",
            credentials=mocked_api_credentials,
            static_discovery=False,
        )
        mocked_sleep.assert_called_once_with(120)

    def test_destroy_modules_in_order(self, mocker: MockFixture) -> None:
        fake_modules = [mocker.Mock(spec=Module) for _ in range(3)]
        for i, module in enumerate(fake_modules):
            module.name = f"fake_module_{i}"

        fake_layer = mocker.Mock(spec=Layer)
        fake_layer.name = "blah"
        fake_layer.cloud = "aws"
        fake_layer.modules = fake_modules

        mocker.patch(
            "opta.core.terraform.Terraform.get_existing_modules",
            return_value={"fake_module_2", "fake_module_1", "fake_module_0"},
        )
        mocker.patch("opta.core.terraform.Terraform.refresh")
        mocker.patch("opta.core.terraform.AWS")
        mocked_cmd = mocker.patch("opta.core.terraform.nice_run")
        Terraform.destroy_all(fake_layer)
        assert get_call_args(mocked_cmd) == [
            ["terraform", "destroy", "-target=module.fake_module_2"],
            ["terraform", "destroy", "-target=module.fake_module_1"],
            ["terraform", "destroy", "-target=module.fake_module_0"],
        ]

        # Additionally verify this works for destroy_resources()
        fake_resources = [
            "module.fake_module_1.bar",
            "module.fake_module_2.foo",
            "module.fake_module_0.baz",
        ]
        mocked_cmd = mocker.patch("opta.core.terraform.nice_run")
        Terraform.destroy_resources(fake_layer, fake_resources)
        assert get_call_args(mocked_cmd) == [
            ["terraform", "destroy", "-target=module.fake_module_2.foo"],
            ["terraform", "destroy", "-target=module.fake_module_1.bar"],
            ["terraform", "destroy", "-target=module.fake_module_0.baz"],
        ]

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
