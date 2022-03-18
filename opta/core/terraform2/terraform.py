# new-module-api

from subprocess import DEVNULL, PIPE  # nosec
from typing import Any, Dict, List, Optional

from opta.nice_subprocess import nice_run


class Terraform:
    def __init__(self) -> None:
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
