from typing import TYPE_CHECKING, Dict, Optional

from opta.core.cloud_client import CloudClient
from opta.exceptions import LocalNotImplemented
from opta.nice_subprocess import nice_run

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class HelmCloudClient(CloudClient):
    def __init__(self, layer: "Layer"):
        super().__init__(layer)

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        return None

    def upload_opta_config(self) -> None:
        return None

    def delete_opta_config(self) -> None:
        return None

    def delete_remote_state(self) -> None:
        return None

    def get_terraform_lock_id(self) -> str:
        return ""

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        raise LocalNotImplemented(
            "get_all_remote_configs: Feature Unsupported for the helm provider"
        )

    def set_kube_config(self) -> None:
        # do nothing, the user brings their own
        pass

    def cluster_exist(self) -> bool:
        # "kubectl version" returns an error code if it can't connect to a cluster
        nice_run(["kubectl", "version"], check=True)
        return True
