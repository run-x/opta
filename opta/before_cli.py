import os
from pathlib import Path

from opta.constants import CI, single_time_data_analytics_prompt
from opta.utils import logger


def data_collection_flag() -> None:
    if os.environ.get(CI) is not None:
        return

    if Path(single_time_data_analytics_prompt).is_file():
        return

    logger.info(
        "****************************IMPORTANT*****************************\n"
        "* By default, Opta executions send metrics and logs back to RunX *\n"
        "* to gain intelligence of the product’s usage, errors, and to    *\n"
        "* give superior support for the users. Like with the stdout      *\n"
        "* users see, these reports do not hold ANY secrets or passwords. *\n"
        "*                                                                *\n"
        "* This is a single time message and would not be shown again.    *\n"
        "*                                                                *\n"
        "* For more information, please go through this Documentation     *\n"
        "*       `https://docs.opta.dev/miscellaneous/analytics/`         *\n"
        "****************************IMPORTANT*****************************"
    )
    open(single_time_data_analytics_prompt, "w").close()


def before_cli() -> None:
    data_collection_flag()
