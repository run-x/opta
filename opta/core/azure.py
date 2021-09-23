import base64
import json
from typing import TYPE_CHECKING, Any, Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, StorageStreamDownloader

from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class Azure:
    project_id: Optional[str] = None

    def __init__(self, layer: "Layer"):
        self.layer = layer

    @classmethod
    def get_credentials(cls) -> Any:
        return DefaultAzureCredential()

    def get_remote_config(self) -> Optional["StructuredConfig"]:
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
            download_stream: StorageStreamDownloader = storage_client.download_blob(
                config_path
            )
            data = download_stream.readall()
            return json.loads(data)
        except Exception:  # Backwards compatibility
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self) -> None:
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
        storage_client.upload_blob(
            name=config_path,
            data=json.dumps(self.layer.structured_config()),
            overwrite=True,
        )

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

    def get_terraform_lock_id(self) -> str:
        providers = self.layer.gen_providers(0)
        credentials = self.get_credentials()
        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]
        container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]
        key = providers["terraform"]["backend"]["azurerm"]["key"]

        try:
            blob = (
                BlobServiceClient(
                    f"https://{storage_account_name}.blob.core.windows.net/",
                    credential=credentials,
                )
                .get_container_client(container_name)
                .get_blob_client(key)
            )
            b64_encoded_tf_lock = blob.get_blob_properties().metadata["Terraformlockid"]
            tf_lock_data = json.loads(base64.b64decode(b64_encoded_tf_lock))
            return tf_lock_data["ID"]
        except ResourceNotFoundError:
            return ""
        except Exception:
            return ""
