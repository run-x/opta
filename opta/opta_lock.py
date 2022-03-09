"""
Usage: This file is used to check if Opta is already running in the current directory.
This creates a file in opta directory with the name: .<pid>.opta.lock
"""


import glob
import os

from opta.exceptions import UserErrors
from opta.utils import logger


def check_opta_running_file_exists() -> bool:
    return glob.glob(os.path.join(os.getcwd(), ".*.opta.lock")).__len__() > 0


def create_opta_lock_file() -> None:
    with open(os.path.join(os.getcwd(), f".{os.getpid()}.opta.lock"), "w") as f:
        f.write("")
    logger.debug(f"Acquired Opta lock on Directory: {os.getcwd()}")


def remove_opta_lock_file() -> None:
    try:
        os.remove(os.path.join(os.getcwd(), f".{os.getpid()}.opta.lock"))
        logger.debug(f"Removed Opta lock on Directory: {os.getcwd()}")
    except FileNotFoundError:
        return


def opta_acquire_lock() -> None:
    if check_opta_running_file_exists():
        raise UserErrors(
            "Opta already running in the current directory.\n"
            "If no opta instance is running, please delete file with mime type .opta.lock"
        )
    create_opta_lock_file()


def opta_release_lock() -> None:
    remove_opta_lock_file()
