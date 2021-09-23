from unittest.mock import Mock

from pytest import fixture
from pytest_mock import MockFixture

from opta.core.azure import Azure
from opta.layer import Layer


@fixture()
def azure_layer() -> Mock:
    layer = Mock(spec=Layer)
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
    return layer


class TestAzure:
    def test_get_credentials(self, mocker: MockFixture) -> None:
        mocked_default_creds = mocker.patch("opta.core.azure.DefaultAzureCredential")
        Azure.get_credentials()
        mocked_default_creds.assert_called_once_with()

    def test_get_remote_config(self, mocker: MockFixture, azure_layer: Mock) -> None:
        mocked_creds = mocker.Mock()
        mocked_default_creds = mocker.patch(
            "opta.core.azure.DefaultAzureCredential", return_value=mocked_creds
        )

        mocked_container_client_instance = mocker.Mock()
        mocked_container_client_instance.download_blob = mocker.Mock()
        download_stream_mock = mocker.Mock()
        download_stream_mock.readall = mocker.Mock(return_value='{"a":1}')
        mocked_container_client_instance.download_blob.return_value = (
            download_stream_mock
        )
        mocked_container_client = mocker.patch(
            "opta.core.azure.ContainerClient",
            return_value=mocked_container_client_instance,
        )

        assert Azure(azure_layer).get_remote_config() == {"a": 1}

        azure_layer.gen_providers.assert_called_once_with(0)
        mocked_default_creds.assert_called_once_with()
        mocked_container_client.assert_called_once_with(
            account_url="https://dummy_storage_account.blob.core.windows.net",
            container_name="dummy_container_name",
            credential=mocked_creds,
        )
        mocked_container_client_instance.download_blob.assert_called_once_with(
            f"opta_config/{azure_layer.name}"
        )

    def test_upload_opta_config(self, mocker: MockFixture, azure_layer: Mock) -> None:
        mocked_creds = mocker.Mock()
        mocked_default_creds = mocker.patch(
            "opta.core.azure.DefaultAzureCredential", return_value=mocked_creds
        )

        mocked_container_client_instance = mocker.Mock()
        mocked_container_client = mocker.patch(
            "opta.core.azure.ContainerClient",
            return_value=mocked_container_client_instance,
        )
        azure_layer.structured_config = mocker.Mock(return_value={"a": 1})

        Azure(azure_layer).upload_opta_config()

        azure_layer.gen_providers.assert_called_once_with(0)
        mocked_default_creds.assert_called_once_with()
        mocked_container_client.assert_called_once_with(
            account_url="https://dummy_storage_account.blob.core.windows.net",
            container_name="dummy_container_name",
            credential=mocked_creds,
        )
        mocked_container_client_instance.upload_blob.assert_called_once_with(
            name=f"opta_config/{azure_layer.name}", data='{"a": 1}', overwrite=True
        )

    def test_delete_opta_config(self, mocker: MockFixture, azure_layer: Mock) -> None:
        mocked_creds = mocker.Mock()
        mocked_default_creds = mocker.patch(
            "opta.core.azure.DefaultAzureCredential", return_value=mocked_creds
        )

        mocked_container_client_instance = mocker.Mock()
        mocked_container_client = mocker.patch(
            "opta.core.azure.ContainerClient",
            return_value=mocked_container_client_instance,
        )

        Azure(azure_layer).delete_opta_config()

        azure_layer.gen_providers.assert_called_once_with(0)
        mocked_default_creds.assert_called_once_with()
        mocked_container_client.assert_called_once_with(
            account_url="https://dummy_storage_account.blob.core.windows.net",
            container_name="dummy_container_name",
            credential=mocked_creds,
        )
        mocked_container_client_instance.delete_blob.assert_called_once_with(
            f"opta_config/{azure_layer.name}", delete_snapshots="include"
        )

    def test_delete_remote_state(self, mocker: MockFixture, azure_layer: Mock) -> None:
        mocked_creds = mocker.Mock()
        mocked_default_creds = mocker.patch(
            "opta.core.azure.DefaultAzureCredential", return_value=mocked_creds
        )

        mocked_container_client_instance = mocker.Mock()
        mocked_container_client = mocker.patch(
            "opta.core.azure.ContainerClient",
            return_value=mocked_container_client_instance,
        )

        Azure(azure_layer).delete_remote_state()

        azure_layer.gen_providers.assert_called_once_with(0)
        mocked_default_creds.assert_called_once_with()
        mocked_container_client.assert_called_once_with(
            account_url="https://dummy_storage_account.blob.core.windows.net",
            container_name="dummy_container_name",
            credential=mocked_creds,
        )
        mocked_container_client_instance.delete_blob.assert_called_once_with(
            azure_layer.name, delete_snapshots="include"
        )
