# new-module-api

import os
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, PIPE  # nosec
from typing import Any, Dict, List, Optional

from opta.exceptions import UserErrors
from opta.layer2 import Layer
from opta.nice_subprocess import nice_run
from opta.utils import json


class Terraform:
    def __init__(self) -> None:
        self.downloaded_state: Dict[str, dict] = {}
        self._init_done: bool = False
        self.ensure_local_state_dir()

    def apply(
        self, *, auto_approve: bool = False, plan: str, quiet: bool = False
    ) -> None:
        self.init()

        flags = self._render_flags(
            {"auto-approve": auto_approve, "compact-warnings": True}
        )

        flags.append(plan)

        self._run("apply", flags, quiet=quiet)

    def download_state(self, layer: Layer) -> bool:
        """
        Temp function to copy state from "local state store"
        """
        # TODO: Return a `State` object that tracks state
        # TODO: Support non-local storage
        state_file: str = "./terraform.tfstate"
        try:
            local_storage_path = self.local_state_filepath(layer)

            if os.path.exists(local_storage_path):
                copyfile(local_storage_path, state_file)

            else:
                return False
        except Exception:
            UserErrors(f"Could not copy local state file to {state_file}")

        with open(state_file, "r") as file:
            raw_state = file.read().strip()

        if raw_state != "":
            self.downloaded_state[layer.name] = json.loads(raw_state)
            return True

        return False

    def upload_state(self, layer: Layer) -> None:
        """
        Temp function to copy state to "local state store"
        """
        state_file = "./terraform.tfstate"
        local_storage_path = self.local_state_filepath(layer)
        copyfile(state_file, local_storage_path)

    def ensure_local_state_dir(self) -> None:
        os.makedirs(self.local_state_dir, exist_ok=True)

    def local_state_filepath(self, layer: Layer) -> str:
        return os.path.join(self.local_state_dir, layer.name)

    @property
    def local_state_dir(self) -> str:
        # TODO: Move to state-store specific code
        return os.path.join(str(Path.home()), ".opta", "local", "tfstate")

    def init(self, quiet: bool = False) -> None:
        if self._init_done:
            return

        self._run("init", quiet=quiet)
        self._init_done = True

    def plan(
        self,
        *,
        lock: bool = True,
        input: bool = False,
        out: Optional[str] = None,
        targets: Optional[List[str]] = None,
        quiet: bool = False,
    ) -> None:
        self.init()

        flags = self._render_flags(
            {"lock": lock, "input": input, "target": targets, "out": out}
        )

        self._run("plan", flags, quiet=quiet)

    def _render_flags(self, flags: Dict[str, Any]) -> List[str]:
        rendered = []
        for key, value in flags.items():
            if value is None:
                continue

            rendered.extend(self._render_flag(key, value))

        return rendered

    def _render_flag(self, key: str, value: Any) -> List[str]:
        if isinstance(value, list):
            return [
                flag for subvalue in value for flag in self._render_flag(key, subvalue)
            ]
        elif isinstance(value, bool):
            if value:
                return [f"-{key}"]

            return [f"-{key}=false"]
        elif isinstance(value, str):
            return [f"-{key}={value}"]

        raise ValueError(f"Unable to add `{key}` to command line")

    def _run(
        self, cmd: str, flags: Optional[List[str]] = None, quiet: bool = False
    ) -> None:
        kwargs: dict = {}
        if quiet:
            kwargs["stderr"] = PIPE
            kwargs["stdout"] = DEVNULL

        if flags is None:
            flags = []

        nice_run(
            ["terraform", cmd, *flags], check=True, **kwargs,
        )
