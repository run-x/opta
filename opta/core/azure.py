import base64
from contextlib import redirect_stderr
from io import StringIO
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, StorageStreamDownloader

from opta.core.cloud_client import CloudClient
from opta.utils import json, logger

if TYPE_CHECKING:
    from opta.layer import StructuredConfig


class Azure(CloudClient):
    project_id: Optional[str] = None
    credentials: Optional[DefaultAzureCredential] = None

    @classmethod
    def get_credentials(cls) -> DefaultAzureCredential:
        if cls.credentials is None:
            cls.credentials = DefaultAzureCredential()
            f = StringIO()
            try:
                with redirect_stderr(f):
                    cls.credentials.get_token("https://storage.azure.com/")
            except ClientAuthenticationError:
                pass
            except Exception as e:
                logger.error(f.getvalue())
                raise e
        return cls.credentials

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

    def list_child_config_names(self) -> List[str]:
        providers = self.layer.gen_providers(0)

        credentials = Azure.get_credentials()
        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]
        container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]
        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=container_name,
            credential=credentials,
        )
        prefix = "opta_config/"
        blobs = storage_client.list_blobs(name_starts_with=prefix)
        configs = [blob.name[len(prefix):] for blob in blobs]
        if self.layer.name in configs:
            configs.remove(self.layer.name)
        return configs

    def get_configuration_details(self, config_name: str) -> Dict[str, Any]:
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
        config_path = f"opta_config/{config_name}"
        download_stream: StorageStreamDownloader = storage_client.download_blob(config_path)
        data = download_stream.readall()
        config_details = json.loads(data)
        return config_details

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

    def bucket_exists(self, bucket_name: str) -> bool:
        providers = self.layer.gen_providers(0)
        credentials = self.get_credentials()
        resource_group_name = providers["terraform"]["backend"]["azurerm"][
            "resource_group_name"
        ]
        storage_account_name = providers["terraform"]["backend"]["azurerm"][
            "storage_account_name"
        ]

        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=bucket_name,
            credential=credentials,
        )
        try:
            storage_client.blob_containers.get(
                resource_group_name, storage_account_name, bucket_name
            )
            return True
        except ResourceNotFoundError:
            return False
