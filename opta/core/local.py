import errno
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from opta.exceptions import UserErrors
from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class Local:
    def __init__(self, layer: "Layer"):
        self.layer = layer
        local_dir = os.path.join(os.path.join(str(Path.home()), ".opta", "local"))

        self.config_file_path = os.path.join(
            local_dir, "opta_config", f"opta-{layer.org_name}-{layer.name}"
        )
        if not os.path.exists(os.path.dirname(self.config_file_path)):
            os.makedirs(os.path.dirname(self.config_file_path))

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        try:
            return json.loads(self.config_file_path)
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

    def delete_local_tf_state(self, org_name, layer_name) -> None:
        tf_file = os.path.join(
            str(Path.home()),
            ".opta",
            "local",
            "tfstate",
            f"opta-tf-state-{org_name}-{layer_name}",
        )
        if os.path.isfile(tf_file):
            os.remove(tf_file)
            logger.info("Deleted opta tf config from local")
        else:
            logger.warn(f"Did not find opta tf state {tf_file} to delete")
