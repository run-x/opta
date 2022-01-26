import os
from shutil import copyfile
from subprocess import DEVNULL, PIPE  # nosec
from typing import Any, Dict, List, Optional

from opta.core.terraform import Terraform as LegacyTerraform
from opta.exceptions import UserErrors
from opta.layer2 import Layer
from opta.nice_subprocess import nice_run
from opta.utils import json


class Terraform:
    def __init__(self) -> None:
        self.downloaded_state: Dict[str, dict] = {}
        self._init_done: bool = False

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
        # TODO: Return a `State` object that tracks state
        # TODO: Support non-local storage
        state_file: str = "./tmp.tfstate"
        try:
            tf_file = os.path.join(
                LegacyTerraform.get_local_opta_dir(), "tfstate", f"{layer.name}",
            )
            if os.path.exists(tf_file):
                copyfile(tf_file, state_file)

            else:
                return False
        except Exception:
            UserErrors(f"Could copy local state file to {state_file}")

        with open(state_file, "r") as file:
            raw_state = file.read().strip()

        os.remove(state_file)
        if raw_state != "":
            self.downloaded_state[layer.name] = json.loads(raw_state)
            return True

        return False

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


class TerraformFile:
    def __init__(self) -> None:
        self.providers: Dict[str, dict] = {}
        self.data: Dict[str, Dict[str, dict]] = {}
        self.required_providers: Dict[str, dict] = {}
        self.backend_id: Optional[str] = None
        self.backend: dict = {}
        self.modules: Dict[str, dict] = {}
        self.outputs: Dict[str, str] = {}

    def add_backend(self, type: str, data: dict) -> None:
        if self.backend_id:
            raise ValueError("Cannot add backend if one is already set")

        self.backend = data
        self.backend_id = type

    def add_data(self, type: str, id: str, data: dict) -> None:
        of_type = self.data.setdefault(type, {})
        if id in of_type:
            raise ValueError(f"Cannot add duplicate data resource {type}.{id}")

        of_type[id] = data

    def add_module(self, id: str, data: dict) -> None:
        if id in self.modules:
            raise ValueError(f"Cannot add duplicate module {id}")

        self.modules[id] = data

    def add_output(self, id: str, data: str) -> None:
        if id in self.outputs:
            raise ValueError(f"Cannot add duplicate output {id}")

        self.outputs[id] = data

    def add_provider(self, id: str, data: dict) -> None:
        if id in self.providers:
            raise ValueError(f"Cannot add duplicate provider {id}")

        self.providers[id] = data

    def add_required_provider(self, id: str, data: dict) -> None:
        if id in self.required_providers:
            raise ValueError(f"Cannot add duplicate required provider {id}")

        self.required_providers[id] = data

    def __to_json__(self) -> dict:
        out: Dict[str, Any] = {}

        if self.data:
            out["data"] = self.data

        if self.required_providers:
            out.setdefault("terraform", {})[
                "required_providers"
            ] = self.required_providers

        if self.backend_id:
            out.setdefault("terraform", {})["backend"] = {
                self.backend_id: self.backend,
            }

        if self.providers:
            out["provider"] = self.providers

        if self.modules:
            out["module"] = self.modules

        if self.outputs:
            out["output"] = {id: {"value": value} for id, value in self.outputs.items()}

        return out
