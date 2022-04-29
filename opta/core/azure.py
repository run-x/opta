import base64
from contextlib import redirect_stderr
from io import StringIO
from subprocess import DEVNULL  # nosec
from typing import TYPE_CHECKING, Dict, Optional

from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, StorageStreamDownloader

from opta.core.cloud_client import CloudClient
from opta.exceptions import AzureNotImplemented
from opta.nice_subprocess import nice_run
from opta.utils import json, logger
from opta.utils.dependencies import ensure_installed

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

    def bucket_exists(self, bucket_name: str, storage_account_name: str) -> bool:
        credentials = self.get_credentials()
        storage_client = ContainerClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            container_name=bucket_name,
            credential=credentials,
        )
        try:
            return storage_client.exists()
        except Exception:
            return False

    def cluster_exist(self) -> bool:
        providers = self.layer.root().gen_providers(0)

        ensure_installed("az")

        rg_name = providers["terraform"]["backend"]["azurerm"]["resource_group_name"]
        subscription_id = providers["provider"]["azurerm"]["subscription_id"]
        cluster_name = self.layer.get_cluster_name()
        try:
            output = nice_run(
                [
                    "az",
                    "aks",
                    "list",
                    "--subscription",
                    subscription_id,
                    "--resource-group",
                    rg_name,
                ],
                capture_output=True,
                check=True,
            ).stdout
            output_list = json.loads(output)
            return any([x.get("name") == cluster_name for x in output_list])
        except Exception:
            return False

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        raise AzureNotImplemented("Feature Unsupported for Azure")

    def get_kube_context_name(self) -> str:
        providers = self.layer.root().gen_providers(0)
        rg_name = providers["terraform"]["backend"]["azurerm"]["resource_group_name"]
        cluster_name = self.layer.get_cluster_name()
        return f"{rg_name}-{cluster_name}-admin"

    def set_kube_config(self) -> None:
        providers = self.layer.root().gen_providers(0)

        ensure_installed("az")

        rg_name = providers["terraform"]["backend"]["azurerm"]["resource_group_name"]
        cluster_name = self.layer.get_cluster_name()
        kube_context_name = self.get_kube_context_name()

        if not self.cluster_exist():
            raise Exception(
                "The AKS cluster name could not be determined -- please make sure it has been applied in the environment."
            )

        nice_run(
            [
                "az",
                "aks",
                "get-credentials",
                "--resource-group",
                rg_name,
                "--name",
                cluster_name,
                "--admin",
                "--overwrite-existing",
                "--context",
                kube_context_name.replace("-admin", ""),
            ],
            stdout=DEVNULL,
            check=True,
        )

    def get_remote_state(self) -> str:
        raise AzureNotImplemented("Feature Unsupported for Azure")
