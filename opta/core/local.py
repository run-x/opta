import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from opta.constants import HOME
from opta.core.cloud_client import CloudClient
from opta.exceptions import LocalNotImplemented
from opta.nice_subprocess import nice_run
from opta.utils import json, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class Local(CloudClient):
    def __init__(self, layer: "Layer"):
        local_dir = os.path.join(os.path.join(str(Path.home()), ".opta", "local"))
        self.tf_file = os.path.join(
            str(Path.home()), ".opta", "local", "tfstate", layer.name
        )
        self.config_file_path = os.path.join(
            local_dir, "opta_config", f"opta-{layer.org_name}-{layer.name}"
        )
        if not os.path.exists(os.path.dirname(self.config_file_path)):
            os.makedirs(os.path.dirname(self.config_file_path))

        super().__init__(layer)

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        try:
            with open(self.config_file_path, "r") as f:
                return json.load(f)
        except Exception:  # Backwards compatibility
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    def upload_opta_config(self) -> None:

        with open(self.config_file_path, "w") as f:
            f.write(json.dumps(self.layer.structured_config()))

        logger.debug("Uploaded opta config to local")

    def delete_opta_config(self) -> None:

        if os.path.isfile(self.config_file_path):
            os.remove(self.config_file_path)
            logger.info("Deleted opta config from local")
        else:
            logger.warning(f"Did not find opta config {self.config_file_path} to delete")

    def delete_remote_state(self) -> None:

        if os.path.isfile(self.tf_file):
            os.remove(self.tf_file)
            logger.info("Deleted opta tf config from local")
        if os.path.isfile(self.tf_file + ".backup"):
            os.remove(self.tf_file + ".backup")
            logger.info("Deleted opta tf backup config from local")
        else:
            logger.warning(f"Did not find opta tf state {self.tf_file} to delete")

    def get_terraform_lock_id(self) -> str:
        return ""

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        raise LocalNotImplemented("Feature Unsupported for Local")

    def get_remote_state(self) -> str:
        raise LocalNotImplemented("Feature Unsupported for Local")

    def set_kube_config(self) -> None:
        nice_run(
            ["kubectl", "config", "use-context", "kind-opta-local-cluster"],
            check=True,
            capture_output=True,
        )

    def get_kube_context_name(self) -> str:
        return "kind-opta-local-cluster"

    def cluster_exist(self) -> bool:
        try:
            output: str = nice_run(
                [f"{HOME}/.opta/local/kind", "get", "clusters"],
                check=True,
                capture_output=True,
            ).stdout
            return output.strip() != ""
        except Exception:
            return False
