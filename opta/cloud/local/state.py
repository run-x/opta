# new-module-api

import os
from pathlib import Path
from typing import List

from opta.core.terraform2 import StateStore, TerraformFile


class LocalStore(StateStore):
    def configure_storage(self) -> None:
        for dir in self._storage_dirs:
            os.makedirs(dir, exist_ok=True)

    def configure_terraform_file(self, tf: TerraformFile) -> None:
        tf.add_backend("local", {"path": str(self._state_path)})

    def is_storage_configured(self) -> bool:
        for dir in self._storage_dirs:
            if not os.path.exists(dir):
                return False

        return True

    def read_raw(self) -> str:
        # TODO: What exception to raise if file not found?
        with open(self._state_path, "r") as f:
            contents = f.read()

        contents = contents.strip()

        return contents

    @property
    def _config_dir(self) -> Path:
        """
        Directory where persisted opta config is stored
        """
        return self._storage_dir / "opta_config"

    @property
    def _config_file_path(self) -> Path:
        """
        File path of the persisted opta config for the current layer
        """
        return self._config_dir / f"opta-{self.config.org_name}-{self.config.layer_name}"

    @property
    def _state_path(self) -> Path:
        """
        File path of the terraform state for the current layer
        """
        return self._state_dir / self.config.layer_name

    @property
    def _state_dir(self) -> Path:
        """
        Directory where terraform state is stored
        """
        return self._storage_dir / "tfstate"

    @property
    def _storage_dir(self) -> Path:
        """
        Root directory of the local opta storage
        """
        return Path.home() / ".opta" / "local"

    @property
    def _storage_dirs(self) -> List[Path]:
        """
        List of all directories that this state store depends on
        """
        return [
            self._config_dir,
            self._storage_dir,
        ]
