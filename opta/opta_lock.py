"""
Usage: This file is used to check if Opta is already running in the current directory.
This creates a file in opta directory with the name: opta_lock_<underscored-cwd>_<pid>
"""


import glob
import os

from opta.constants import HOME
from opta.exceptions import UserErrors
from opta.utils import logger

OPTA_LOCK_LOC_PREFIX = os.path.join(
    HOME, ".opta", f"opta_lock_{os.getcwd().replace(os.path.sep, '_')}_"
)


def check_opta_running_file_exists() -> bool:
    return glob.glob(OPTA_LOCK_LOC_PREFIX + "*").__len__() > 0


def create_opta_lock_file() -> None:
    with open(f"{OPTA_LOCK_LOC_PREFIX}_{os.getpid()}", "w") as f:
        f.write("")
    logger.debug(f"Acquired Opta lock on Directory: {os.getcwd()}")


def remove_opta_lock_file() -> None:
    try:
        os.remove(f"{OPTA_LOCK_LOC_PREFIX}_{os.getpid()}")
        logger.debug(f"Removed Opta lock on Directory: {os.getcwd()}")
    except FileNotFoundError:
        pass


def opta_acquire_lock() -> None:
    if check_opta_running_file_exists():
        raise UserErrors("Opta already running in the current directory.")
    create_opta_lock_file()


def opta_release_lock() -> None:
    remove_opta_lock_file()
