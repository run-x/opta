import os
import sys
from pathlib import Path

import click
from click import Abort

from opta.constants import CI, OPTA_DISABLE_REPORTING, data_analytics_prompt
from opta.utils import logger


def data_collection_flag() -> None:
    if os.environ.get(CI) is not None or os.environ.get(OPTA_DISABLE_REPORTING):
        return

    if Path(data_analytics_prompt).is_file():
        return

    logger.info(
        "\n"
        "|---------------------------IMPORTANT----------------------------|\n"
        "| By default, Opta executions send metrics and logs back to RunX |\n"
        "| to gain intelligence of the product’s usage, errors, and to    |\n"
        "| give superior support for the users. Like with the stdout      |\n"
        "| users see, these reports do not hold ANY secrets or passwords. |\n"
        "|                                                                |\n"
        "| For more information, and how to disable the Metric Collection |\n"
        "| please go through this Documentation below.                    |\n"
        "| `https://docs.opta.dev/miscellaneous/analytics/`               |\n"
        "|---------------------------IMPORTANT----------------------------|\n"
    )
    try:
        click.confirm("Do you consent to RunX tracking your data?", abort=True)
        open(data_analytics_prompt, "w").close()
    except Abort:
        logger.error(
            "\n"
            "|-----------------------------ERROR------------------------------|\n"
            "| Please follow the steps mentioned in the above Documentation   |\n"
            "| to disable the Metrics and Logs Tracking and try again.        |\n"
            "|-----------------------------ERROR------------------------------|\n"
        )
        sys.exit(0)


def before_cli() -> None:
    data_collection_flag()
