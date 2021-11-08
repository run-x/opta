import os
from typing import Tuple

from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run


def symlink_check() -> None:
    is_symlink, cwd_path = is_symlinked_path()
    if is_symlink:
        raise UserErrors(
            f"Opta doesn't support running from a Symlinked Directory, "
            f"and the current directory seems to be a Symbolic Link.\n"
            f"Please run from a non-Symlinked Directory. "
            f"Actual Path of current Symlinked Path: {cwd_path}"
        )


def is_symlinked_path() -> Tuple[bool, str]:
    pwd_path = (
        nice_run(["pwd"], capture_output=True, shell=True)  # nosec
        .stdout.decode("utf-8")
        .strip()
    )
    cwd_path = os.getcwd()

    return pwd_path != cwd_path, cwd_path
