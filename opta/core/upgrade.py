import os
import random

import requests
import semver

from opta.constants import DEV_VERSION, VERSION
from opta.utils import logger
from opta.utils.globals import OptaUpgrade

LATEST_VERSION_FILE_URL = "https://dev-runx-opta-binaries.s3.amazonaws.com/latest"
UPGRADE_CHECK_PROBABILITY: float = float(
    os.environ.get("OPTA_UPGRADE_CHECK_PROBABILITY", "0.2")
)
# TODO: Change this to the actual upgrade URL.
UPGRADE_INSTRUCTIONS_URL = "https://docs.opta.dev/installation/"


def _should_check_for_version_upgrade() -> bool:
    return (VERSION not in [DEV_VERSION, "", None]) and (
        random.random() < UPGRADE_CHECK_PROBABILITY  # nosec
    )


def _get_latest_version() -> str:
    logger.debug(f"Querying {LATEST_VERSION_FILE_URL}")
    resp = requests.get(LATEST_VERSION_FILE_URL)
    resp.raise_for_status()
    return resp.text.strip().strip("v")


def disable_version_upgrade() -> None:
    global UPGRADE_CHECK_PROBABILITY
    UPGRADE_CHECK_PROBABILITY = 0


def check_version_upgrade(is_upgrade_call: bool = False) -> bool:
    """Logs a warning if newer version of opta is available.

    The version check is not always performed when this function is called.
    It is performed non-deterministically with a probability of UPGRADE_CHECK_PROBABILITY
    in order to not spam the user.
    """
    if OptaUpgrade.successful:
        OptaUpgrade.unset()
        return True
    if is_upgrade_call or _should_check_for_version_upgrade():
        logger.info("Checking for version upgrades...")
        try:
            latest_version = _get_latest_version()
        except Exception as e:
            logger.debug(e, exc_info=True)
            logger.info("Unable to find latest version.")
            return False
        try:
            if semver.VersionInfo.parse(VERSION.strip("v")).compare(latest_version) < 0:
                logger.warning(
                    "New version available.\n"
                    f"You have {VERSION} installed. Latest version is {latest_version}."
                )
                if not is_upgrade_call:
                    print(
                        f"Upgrade instructions are available at {UPGRADE_INSTRUCTIONS_URL}  or simply use the `opta upgrade` command"
                    )
                return True
            else:
                logger.info("User on the latest version.")
        except Exception as e:
            logger.info(f"Semver check failed with error {e}")
    return False
