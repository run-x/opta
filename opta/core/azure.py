from typing import TYPE_CHECKING, Any, Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient

from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer


class Azure:
    project_id: Optional[str] = None

    def __init__(self, layer: "Layer"):
        self.layer = layer

    @classmethod
    def get_credentials(cls) -> Any:
        return DefaultAzureCredential()

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self, config_data: str) -> None:
        providers = self.layer.gen_providers(0)
        credentials = self.get_credentials()

        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]
        container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]

        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=container_name,
            credential=credentials,
        )
        config_path = f"opta_config/{self.layer.name}"
        storage_client.upload_blob(name=config_path, data=config_data, overwrite=True)

    def delete_opta_config(self) -> None:
        providers = self.layer.gen_providers(0)
        credentials = self.get_credentials()

        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]
        container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]

        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=container_name,
            credential=credentials,
        )
        config_path = f"opta_config/{self.layer.name}"
        try:
            storage_client.delete_blob(config_path, delete_snapshots="include")
        except ResourceNotFoundError:
            logger.info("Remote opta config was already deleted")

    def delete_remote_state(self) -> None:
        providers = self.layer.gen_providers(0)
        credentials = self.get_credentials()

        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]
        container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]

        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=container_name,
            credential=credentials,
        )
        config_path = f"{self.layer.name}"
        try:
            storage_client.delete_blob(config_path, delete_snapshots="include")
        except ResourceNotFoundError:
            logger.info("Remote opta state was already deleted")
