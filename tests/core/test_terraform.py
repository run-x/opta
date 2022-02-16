from typing import List

import pytest
from botocore.exceptions import ClientError
from google.api_core.exceptions import ClientError as GoogleClientError
from pytest_mock import MockFixture

from opta.core.terraform import Terraform, fetch_terraform_state_resources
from opta.exceptions import UserErrors
from opta.layer import Layer


class TestTerraform:
    def test_init(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.nice_run")

        # Calling terraform apply should also call terraform init
        tf_init = mocker.patch("opta.core.terraform.Terraform.init")
        fake_layer = mocker.Mock(spec=Layer)
        fake_layer.cloud = "blah"
        Terraform.apply(layer=fake_layer)
        assert tf_init.call_count == 1

        # Calling terraform plan should also call terraform init
        Terraform.plan(layer=fake_layer)
        assert tf_init.call_count == 2

    def test_validate_version_good(self, mocker: MockFixture) -> None:
        ensure_installed = mocker.patch("opta.core.terraform.ensure_installed")
        get_version = mocker.patch("opta.core.terraform.Terraform.get_version")
        get_version.return_value = "1.0.0"

        Terraform.validate_version()

        ensure_installed.assert_called_once_with("terraform")
        get_version.assert_called_once()

    def test_validate_version_missing(self, mocker: MockFixture) -> None:
        ensure_installed = mocker.patch(
            "opta.core.terraform.ensure_installed", side_effect=UserErrors("foobar")
        )
        get_version = mocker.patch("opta.core.terraform.Terraform.get_version")

        with pytest.raises(UserErrors) as e:
            Terraform.validate_version()

        ensure_installed.assert_called_once_with("terraform")
        assert str(e.value) == "foobar"

        get_version.assert_not_called()

    def test_validate_version_low(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.ensure_installed")
        get_version = mocker.patch("opta.core.terraform.Terraform.get_version")
        get_version.return_value = "0.14.9"

        with pytest.raises(UserErrors) as e:
            Terraform.validate_version()

        assert (
            str(e.value)
            == "Invalid terraform version 0.14.9 -- must be at least 0.15.0. Check https://docs.opta.dev/installation/#prerequisites"
        )
        get_version.assert_called_once()

    def test_validate_version_high(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.terraform.ensure_installed")
        get_version = mocker.patch("opta.core.terraform.Terraform.get_version")
        get_version.return_value = "2.0.0"

        with pytest.raises(UserErrors) as e:
            Terraform.validate_version()

        assert (
            str(e.value)
            == "Invalid terraform version 2.0.0 -- must be less than 2.0.0. Check https://docs.opta.dev/installation/#prerequisites"
        )
        get_version.assert_called_once()

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
        mocked_layer.cloud = "blah"
        assert {"redis", "doc_db"} == Terraform.get_existing_modules(mocked_layer)

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
        read_data = '{"a": 1}'
        mocked_file = mocker.mock_open(read_data=read_data)
        mocker.patch("opta.core.terraform.os.remove")
        mocked_open = mocker.patch("opta.core.terraform.open", mocked_file)

        assert Terraform.download_state(layer)
        layer.gen_providers.assert_called_once_with(0)
        mocked_s3_client.download_file.assert_called_once_with(
            Bucket="opta-tf-state-test-dev1", Key="dev1", Filename="./tmp.tfstate"
        )
        mocked_open.assert_called_once_with("./tmp.tfstate", "r")
        patched_init.assert_not_called()
        mocked_boto_client.assert_called_once_with("s3", config=mocker.ANY)

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
        read_data = '{"a": 1}'
        mocked_file = mocker.mock_open(read_data=read_data)
        mocker.patch("opta.core.terraform.os.remove")
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
        mocked_open.assert_has_calls(
            [mocker.call("./tmp.tfstate", "wb"), mocker.call("./tmp.tfstate", "r")],
            any_order=True,
        )
        mocked_storage_client.download_blob_to_file.assert_called_once_with(
            mocker.ANY, mocker.ANY
        )

    def test_azure_download_state(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "azurerm"
        layer.name = "blah"
        layer.providers = {
            "azurerm": {
                "location": "centralus",
                "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
            }
        }
        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "azurerm": {
                        "resource_group_name": "dummy_resource_group",
                        "storage_account_name": "dummy_storage_account",
                        "container_name": "dummy_container_name",
                        "key": "dummy_key",
                    }
                }
            },
            "provider": {
                "azurerm": {
                    "location": "centralus",
                    "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                    "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
                }
            },
        }
        mocked_azure = mocker.patch("opta.core.terraform.Azure")
        mocked_credentials = mocker.Mock()
        mocked_azure.get_credentials.return_value = mocked_credentials
        mocker.patch(
            "opta.core.terraform.Terraform._azure_verify_storage", return_value=True
        )
        mocked_blob_service_client_instance = mocker.Mock()
        mocked_blob_service_client = mocker.patch(
            "opta.core.terraform.BlobServiceClient",
            return_value=mocked_blob_service_client_instance,
        )
        mocked_container_client = mocker.Mock()
        mocked_blob_service_client_instance.get_container_client.return_value = (
            mocked_container_client
        )
        mocked_blob_client = mocker.Mock()
        mocked_container_client.get_blob_client.return_value = mocked_blob_client
        read_data = '{"a": 1}'
        mocked_file = mocker.mock_open(read_data=read_data)
        mocker.patch("opta.core.terraform.os.remove")
        mocked_open = mocker.patch("opta.core.terraform.open", mocked_file)

        assert Terraform.download_state(layer)

        mocked_blob_service_client.assert_called_once_with(
            "https://dummy_storage_account.blob.core.windows.net/",
            credential=mocked_credentials,
        )
        mocked_blob_service_client_instance.get_container_client.assert_called_once_with(
            "dummy_container_name"
        )
        mocked_container_client.get_blob_client.assert_called_once_with("dummy_key")
        mocked_open.assert_has_calls(
            [mocker.call("./tmp.tfstate", "wb"), mocker.call("./tmp.tfstate", "r")],
            any_order=True,
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

        layer.gen_providers.assert_called_once_with(0, clean=False)
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
        # Visit (https://run-x.atlassian.net/browse/RUNX-1125) for further reference
        mocked_boto3.client.assert_has_calls(
            [
                mocker.call("s3", config=mocker.ANY),
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
        mocked_bucket = mocker.Mock()
        mocked_bucket.project_number = "123"
        mocked_storage_client.create_bucket.return_value = mocked_bucket

        mocked_google_credentials = mocker.patch("opta.core.terraform.GoogleCredentials")
        mocked_api_credentials = mocker.Mock()
        mocked_google_credentials.get_application_default.return_value = (
            mocked_api_credentials
        )
        mocked_discovery = mocker.patch("opta.core.terraform.discovery")
        mocked_service = mocker.Mock()
        mocked_cloudresourcemanager = mocker.Mock()
        mocked_discovery.build.side_effect = [mocked_service, mocked_cloudresourcemanager]
        mocked_service_services = mocker.Mock()
        mocked_service.services.return_value = mocked_service_services
        mocked_request = mocker.Mock()
        mocked_service_services.enable.return_value = mocked_request
        mocked_response: dict = {}
        mocked_request.execute.return_value = mocked_response
        mocked_sleep = mocker.patch("opta.core.terraform.time.sleep")

        mocked_cloudresourcemanager_projects = mocker.Mock()
        mocked_cloudresourcemanager.projects.return_value = (
            mocked_cloudresourcemanager_projects
        )
        mocked_cloudresourcemanager_request = mocker.Mock()
        mocked_cloudresourcemanager_projects.get.return_value = (
            mocked_cloudresourcemanager_request
        )
        mocked_cloudresourcemanager_response: dict = {"projectNumber": "123"}
        mocked_cloudresourcemanager_request.execute.return_value = (
            mocked_cloudresourcemanager_response
        )

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
        mocked_discovery.build.assert_has_calls(
            [
                mocker.call(
                    "serviceusage",
                    "v1",
                    credentials=mocked_api_credentials,
                    static_discovery=False,
                ),
                mocker.call(
                    "cloudresourcemanager",
                    "v1",
                    credentials=mocked_api_credentials,
                    static_discovery=False,
                ),
            ]
        )
        mocked_sleep.assert_called_once_with(120)

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

    def test_azure_verify_storage(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "azurerm"
        layer.name = "blah"
        layer.providers = {
            "azurerm": {
                "location": "centralus",
                "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
            }
        }
        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "azurerm": {
                        "resource_group_name": "dummy_resource_group",
                        "storage_account_name": "dummy_storage_account",
                        "container_name": "dummy_container_name",
                    }
                }
            },
            "provider": {
                "azurerm": {
                    "location": "centralus",
                    "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                    "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
                }
            },
        }
        mocked_azure = mocker.patch("opta.core.terraform.Azure")  # noqa: F841

        assert Terraform._azure_verify_storage(layer)

    def test_create_azure_state_storage(self, mocker: MockFixture) -> None:
        layer = mocker.Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "azurerm"
        layer.name = "blah"
        layer.providers = {
            "azurerm": {
                "location": "centralus",
                "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
            }
        }
        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "azurerm": {
                        "resource_group_name": "dummy_resource_group",
                        "storage_account_name": "dummy_storage_account",
                        "container_name": "dummy_container_name",
                    }
                }
            },
            "provider": {
                "azurerm": {
                    "location": "centralus",
                    "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                    "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
                }
            },
        }
        mocked_azure = mocker.patch("opta.core.terraform.Azure")
        mocked_credentials = mocker.Mock()
        mocked_azure.get_credentials.return_value = mocked_credentials
        mocked_resource_client_instance = mocker.Mock()
        mocked_resource_client = mocker.patch(
            "opta.core.terraform.ResourceManagementClient",
            return_value=mocked_resource_client_instance,
        )
        mocked_rg_result = mocker.Mock()
        mocked_rg_result.name = "dummy_resource_group"
        mocked_rg_result.id = "resource_group_id"
        mocked_resource_client_instance.resource_groups.create_or_update.return_value = (
            mocked_rg_result
        )

        mocked_authorization_management_client_instance = mocker.Mock()
        mocked_authorization_management_client = mocker.patch(
            "opta.core.terraform.AuthorizationManagementClient",
            return_value=mocked_authorization_management_client_instance,
        )
        mocked_owner_role = mocker.Mock()
        mocked_owner_role.id = "owner_role_id"
        storage_role = mocker.Mock()
        storage_role.id = "storage_role_id"
        key_vault_role = mocker.Mock()
        key_vault_role.id = "key_vault_role_id"
        mocked_authorization_management_client_instance.role_definitions.list.side_effect = [
            [mocked_owner_role],
            [storage_role],
            [key_vault_role],
        ]
        role_assignment = mocker.Mock()
        role_assignment.role_definition_id = "owner_role_id"
        mocked_authorization_management_client_instance.role_assignments.list_for_resource_group.return_value = [
            role_assignment
        ]

        mocked_storage_client_instance = mocker.Mock()
        mocked_storage_client = mocker.patch(
            "opta.core.terraform.StorageManagementClient",
            return_value=mocked_storage_client_instance,
        )

        Terraform.create_state_storage(layer)

        mocked_azure.get_credentials.assert_called_once_with()
        mocked_resource_client.assert_called_once_with(
            mocked_credentials, "blah99ae-blah-blah-blah-blahd2a04788"
        )
        mocked_authorization_management_client.assert_called_once_with(
            mocked_credentials,
            "blah99ae-blah-blah-blah-blahd2a04788",
            api_version="2018-01-01-preview",
        )
        mocked_resource_client_instance.resource_groups.create_or_update.assert_called_once_with(
            "dummy_resource_group", {"location": "centralus"}
        )
        mocked_authorization_management_client_instance.role_definitions.list.assert_has_calls(
            [
                mocker.call("resource_group_id", filter="roleName eq 'Owner'"),
                mocker.call(
                    "resource_group_id", filter="roleName eq 'Storage Blob Data Owner'"
                ),
                mocker.call(
                    "resource_group_id", filter="roleName eq 'Key Vault Administrator'"
                ),
            ],
            any_order=True,
        )
        mocked_authorization_management_client_instance.role_assignments.list_for_resource_group.assert_called_once_with(
            "dummy_resource_group"
        )
        mocked_authorization_management_client_instance.role_assignments.create.assert_has_calls(
            [
                mocker.call(
                    scope="/subscriptions/blah99ae-blah-blah-blah-blahd2a04788/resourceGroups/dummy_resource_group",
                    role_assignment_name=mocker.ANY,
                    parameters={
                        "role_definition_id": storage_role.id,
                        "principal_id": role_assignment.principal_id,
                    },
                ),
                mocker.call(
                    scope="/subscriptions/blah99ae-blah-blah-blah-blahd2a04788/resourceGroups/dummy_resource_group",
                    role_assignment_name=mocker.ANY,
                    parameters={
                        "role_definition_id": key_vault_role.id,
                        "principal_id": role_assignment.principal_id,
                    },
                ),
            ],
            any_order=True,
        )
        mocked_storage_client.assert_called_once_with(
            mocked_credentials, "blah99ae-blah-blah-blah-blahd2a04788"
        )
        mocked_storage_client_instance.storage_accounts.get_properties.assert_called_once_with(
            "dummy_resource_group", "dummy_storage_account"
        )
        mocked_storage_client_instance.blob_containers.get.assert_called_once_with(
            "dummy_resource_group", "dummy_storage_account", "dummy_container_name"
        )

    def test_force_unlock_aws(self, mocker: MockFixture) -> None:
        tf_flags: List[str] = ["-force"]

        mock_layer = mocker.Mock(spec=Layer)
        mock_layer.gen_providers.return_value = {
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

        mocker.patch("opta.core.terraform.AWS")
        mock_get_aws_lock_id = mocker.patch(
            "opta.core.terraform.Terraform._get_aws_lock_id",
            return_value="mock_aws_lock_id",
        )
        mock_force_unlock_nice_run = mocker.patch("opta.core.terraform.nice_run")

        Terraform.force_unlock(mock_layer, *tf_flags)

        mock_layer.gen_providers.assert_called_once_with(0, clean=False)
        mock_get_aws_lock_id.assert_called_once_with(mock_layer)
        mock_force_unlock_nice_run.assert_called_once_with(
            ["terraform", "force-unlock", *tf_flags, mock_get_aws_lock_id.return_value],
            check=True,
            use_asyncio_nice_run=True,
        )

    def test_force_unlock_gcp(self, mocker: MockFixture) -> None:
        mock_layer = mocker.Mock(spec=Layer)
        mock_layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "gcs": {"bucket": "opta-tf-state-test-dev1", "prefix": "dev1"}
                }
            },
            "provider": {"google": {"region": "us-central1", "project": "dummy-project"}},
        }

        mocker.patch("opta.core.terraform.GCP")
        mock_get_gcp_lock_id = mocker.patch(
            "opta.core.terraform.Terraform._get_gcp_lock_id",
            return_value="mock_gcp_lock_id",
        )
        mock_force_unlock_nice_run = mocker.patch("opta.core.terraform.nice_run")

        Terraform.force_unlock(mock_layer)

        mock_layer.gen_providers.assert_called_once_with(0, clean=False)
        mock_get_gcp_lock_id.assert_called_once_with(mock_layer)
        mock_force_unlock_nice_run.assert_called_once_with(
            ["terraform", "force-unlock", mock_get_gcp_lock_id.return_value],
            check=True,
            use_asyncio_nice_run=True,
        )

    def test_force_unlock_azure(self, mocker: MockFixture) -> None:
        mock_layer = mocker.Mock(spec=Layer)
        mock_layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "azurerm": {
                        "resource_group_name": "dummy_resource_group",
                        "storage_account_name": "dummy_storage_account",
                        "container_name": "dummy_container_name",
                    }
                }
            },
            "provider": {
                "azurerm": {
                    "location": "centralus",
                    "tenant_id": "blahbc17-blah-blah-blah-blah291d395b",
                    "subscription_id": "blah99ae-blah-blah-blah-blahd2a04788",
                }
            },
        }

        mocker.patch("opta.core.terraform.GCP")
        mock_get_azure_lock_id = mocker.patch(
            "opta.core.terraform.Terraform._get_azure_lock_id",
            return_value="mock_azure_lock_id",
        )
        mock_force_unlock_nice_run = mocker.patch("opta.core.terraform.nice_run")

        Terraform.force_unlock(mock_layer)

        mock_layer.gen_providers.assert_called_once_with(0, clean=False)
        mock_get_azure_lock_id.assert_called_once_with(mock_layer)
        mock_force_unlock_nice_run.assert_called_once_with(
            ["terraform", "force-unlock", mock_get_azure_lock_id.return_value],
            check=True,
            use_asyncio_nice_run=True,
        )

    def test_force_unlock_no_lock_id(self, mocker: MockFixture) -> None:
        mock_layer = mocker.Mock(spec=Layer)
        mock_layer.gen_providers.return_value = {
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

        mocker.patch("opta.core.terraform.AWS")
        mock_get_aws_lock_id = mocker.patch(
            "opta.core.terraform.Terraform._get_aws_lock_id", return_value="",
        )
        mock_force_unlock_nice_run = mocker.patch("opta.core.terraform.nice_run")

        Terraform.force_unlock(mock_layer)

        mock_layer.gen_providers.assert_called_once_with(0, clean=False)
        mock_get_aws_lock_id.assert_called_once_with(mock_layer)
        mock_force_unlock_nice_run.assert_not_called()
