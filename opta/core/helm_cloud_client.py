import os
from typing import TYPE_CHECKING, Dict, Optional

from opta.constants import REGISTRY
from opta.core.cloud_client import CloudClient
from opta.exceptions import LocalNotImplemented
from opta.nice_subprocess import nice_run
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class HelmCloudClient(CloudClient):
    def __init__(self, layer: "Layer"):
        super().__init__(layer)

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        return None

    def upload_opta_config(self) -> None:
        if "local" in REGISTRY[self.layer.cloud]["backend"]:
            providers = self.layer.gen_providers(0)
            local_path = providers["terraform"]["backend"]["local"]["path"]
            real_path = os.path.dirname(os.path.realpath(local_path))
            logger.warning(
                f"The terraform state is stored locally, make sure to keep the files in {real_path}"
            )
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

    def get_kube_context_name(self) -> str:
        return nice_run(
            ["kubectl", "config", "current-context"], check=True, capture_output=True
        ).stdout.strip()

    def get_remote_state(self) -> str:
        pass
