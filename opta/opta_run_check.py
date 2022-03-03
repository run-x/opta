"""
Usage: This file is used to check if Opta is already running in the current directory.
This creates a file in opta directory with the name: .opta_running_<underscored-cwd>_<pid>
"""


import glob
import os

from opta.constants import HOME
from opta.exceptions import UserErrors

OPTA_RUNNING_LOC_PREFIX = os.path.join(
    HOME, ".opta", f".opta_running_{os.getcwd().replace(os.path.sep, '_')}_"
)


def check_opta_running_file_exists() -> bool:
    return glob.glob(OPTA_RUNNING_LOC_PREFIX + "*").__len__() > 0


def create_opta_running_file() -> None:
    with open(f"{OPTA_RUNNING_LOC_PREFIX}_{os.getpid()}", "w") as f:
        f.write("")


def remove_opta_running_file() -> None:
    try:
        os.remove(f"{OPTA_RUNNING_LOC_PREFIX}_{os.getpid()}")
    except FileNotFoundError:
        pass


def opta_run_start() -> None:
    if check_opta_running_file_exists():
        raise UserErrors("Opta already running in the current directory.")
    create_opta_running_file()


def opta_run_end() -> None:
    remove_opta_running_file()
