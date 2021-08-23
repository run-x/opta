import os
from pathlib import Path

from opta.constants import CI, OPTA_DISABLE_REPORTING, data_analytics_prompt
from opta.utils import logger


def data_collection_flag() -> None:
    if os.environ.get(CI) is not None or os.environ.get(OPTA_DISABLE_REPORTING):
        return

    if Path(data_analytics_prompt).is_file():
        return

    logger.info(
        "\n"
        "Opta logs usage analytics to improve the user experience \n"
        "To disable it, checkout the instructions in the documentation: `https://docs.opta.dev. \n"
    )


def before_cli() -> None:
    data_collection_flag()
