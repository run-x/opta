import os

import click
import requests

from opta.constants import OPTA_INSTALL_URL
from opta.core.upgrade import check_version_upgrade
from opta.nice_subprocess import nice_run
from opta.utils import logger
from opta.utils.globals import OptaUpgrade

TEMP_INSTALLATION_FILENAME = "opta_installation.sh"


def _make_installation_file() -> None:
    logger.debug(f"Querying {OPTA_INSTALL_URL}")
    resp = requests.get(OPTA_INSTALL_URL)
    resp.raise_for_status()
    with open(TEMP_INSTALLATION_FILENAME, "w") as file:
        file.write(resp.text)
    nice_run(["chmod", "777", TEMP_INSTALLATION_FILENAME])


def _upgrade_successful() -> None:
    OptaUpgrade.success()


def _cleanup_installation_file() -> None:
    if os.path.isfile(TEMP_INSTALLATION_FILENAME):
        os.remove(TEMP_INSTALLATION_FILENAME)


@click.command()
def upgrade() -> None:
    """
    Upgrade Opta to the latest version available
    """
    _upgrade()


def _upgrade() -> None:
    try:
        upgrade_present = check_version_upgrade(is_upgrade_call=True)
        if upgrade_present:
            _make_installation_file()
            nice_run([f"./{TEMP_INSTALLATION_FILENAME}"], input=b"y")
            _upgrade_successful()
    except Exception:
        logger.error(
            "\nUnable to install latest version of Opta."
            "\nPlease follow the instructions on http://run-x.github.io/installation"
        )
    finally:
        _cleanup_installation_file()
