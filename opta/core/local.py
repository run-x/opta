import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from opta.core.cloud_client import CloudClient
from opta.exceptions import UserErrors
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
            return json.load(open(self.config_file_path, "r"))
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
            logger.warn(f"Did not find opta config {self.config_file_path} to delete")

    def delete_remote_state(self) -> None:

        if os.path.isfile(self.tf_file):
            os.remove(self.tf_file)
            logger.info("Deleted opta tf config from local")
        if os.path.isfile(self.tf_file + ".backup"):
            os.remove(self.tf_file + ".backup")
            logger.info("Deleted opta tf backup config from local")
        else:
            logger.warn(f"Did not find opta tf state {self.tf_file} to delete")

    def get_terraform_lock_id(self) -> str:
        return ""

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        raise UserErrors("Feature Unsupported for Local")
