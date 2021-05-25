import random

import requests
import semver

from opta.constants import DEV_VERSION, VERSION
from opta.utils import logger

LATEST_VERSION_FILE_URL = "https://dev-runx-opta-binaries.s3.amazonaws.com/latest"
UPGRADE_CHECK_PROBABILITY = 0.2
# TODO: Change this to the actual upgrade URL.
UPGRADE_INSTRUCTIONS_URL = "https://docs.runx.dev/docs/installation/"


def _should_check_for_version_upgrade() -> bool:
    return (VERSION != DEV_VERSION) and (
        random.random() < UPGRADE_CHECK_PROBABILITY  # nosec
    )


def _get_latest_version() -> str:
    logger.debug(f"Querying {LATEST_VERSION_FILE_URL}")
    resp = requests.get(LATEST_VERSION_FILE_URL)
    resp.raise_for_status()
    return resp.text.strip().strip("v")


def check_version_upgrade() -> None:
    """Logs a warning if newer version of opta is available.

    The version check is not always performed when this function is called.
    It is performed non-deterministically with a probability of UPGRADE_CHECK_PROBABILITY
    in order to not spam the user.
    """
    if not _should_check_for_version_upgrade():
        return
    logger.info("Checking for version upgrades...")
    try:
        latest_version = _get_latest_version()
    except Exception as e:
        logger.debug(e, exc_info=True)
        logger.info("Unable to find latest version.")
        return
    if semver.VersionInfo.parse(VERSION).compare(latest_version) < 0:
        logger.warning(
            "New version available.\n"
            f"You have {VERSION} installed. Latest version is {latest_version}.\n"
            f"Upgrade instructions are available at {UPGRADE_INSTRUCTIONS_URL}."
        )
    else:
        logger.info("You are running the latest version of opta.")
