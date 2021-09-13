import errno
import json
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from opta.exceptions import UserErrors
from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class Local:
    def __init__(self, layer: "Layer"):
        self.layer = layer
        self.state_path = self.layer.providers["local"]["state_path"]
        self.config_file_path = os.path.join(self.state_path, self.layer.name, "config")
        if not os.path.exists(os.path.dirname(self.config_file_path)):
            try:
                os.makedirs(os.path.dirname(self.config_file_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.tfstate_path = os.path.join(
            self.state_path, self.layer.name, "default.tfstate"
        )
        if not os.path.exists(os.path.dirname(self.tfstate_path)):
            try:
                os.makedirs(os.path.dirname(self.tfstate_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

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

        if os.path.exists(self.config_file_path):
            os.remove(self.config_file_path)
            logger.info("Deleted opta config from local")
        else:
            logger.warn(f"Did not find opta config {self.config_file_path} to delete")

    def delete_remote_state(self) -> None:
        if os.path.exists(self.tfstate_path):
            os.remove(self.tfstate_path)
            logger.info("Deleted opta config from local")
        else:
            logger.warn(f"Did not find opta tf state {self.tfstate_path} to delete")
