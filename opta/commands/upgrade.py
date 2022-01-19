import os

import click
import requests
from colored import attr, fg

from opta.constants import OPTA_INSTALL_URL, successfull_upgrade
from opta.nice_subprocess import nice_run
from opta.upgrade import check_version_upgrade
from opta.utils import logger

TEMP_INSTALLATION_FILENAME = "opta_installation.sh"


def _make_installation_file() -> None:
    logger.debug(f"Querying {OPTA_INSTALL_URL}")
    resp = requests.get(OPTA_INSTALL_URL)
    resp.raise_for_status()
    with open(TEMP_INSTALLATION_FILENAME, "w") as file:
        file.write(resp.text)
    nice_run(["chmod", "777", TEMP_INSTALLATION_FILENAME])


def _upgrade_successfull() -> None:
    open(successfull_upgrade, "w").close()


def _cleanup_installation_file() -> None:
    if os.path.isfile(TEMP_INSTALLATION_FILENAME):
        os.remove(TEMP_INSTALLATION_FILENAME)


@click.command()
def upgrade() -> None:
    """
    Upgrade Opta to the Latest version available
    """
    try:
        upgrade_present = check_version_upgrade(is_upgrade_call=True)
        if upgrade_present:
            _make_installation_file()
            os.system(f"yes 2>/dev/null | ./{TEMP_INSTALLATION_FILENAME}")
            _upgrade_successfull()
    except Exception:
        logger.error(
            f"{fg('red')}"
            "\nUnable to Install Latest Version of Opta."
            "\nPlease follow the Instructions on https://docs.opta.dev/installation"
            f"{attr(0)}"
        )
    finally:
        _cleanup_installation_file()
