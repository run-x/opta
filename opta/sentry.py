import os
import platform
import sys
from typing import Any

import sentry_sdk
from getmac import get_mac_address
from git.config import GitConfigParser
from sentry_sdk.integrations.atexit import AtexitIntegration

from opta.constants import VERSION
from opta.exceptions import UserErrors
from opta.utils import logger


def at_exit_callback(pending: int, timeout: float) -> None:
    """Don't be loud about sentry, our customer doesn't care about it."""

    def echo(msg):
        # type: (str) -> None
        sys.stderr.write(msg + "\n")

    if pending > 0:
        echo("Sentry is attempting to send %i pending error messages" % pending)
        echo("Waiting up to %s seconds" % timeout)
        echo("Press Ctrl-%s to quit" % (os.name == "nt" and "Break" or "C"))
    sys.stderr.flush()


def before_send(event: Any, hint: Any) -> Any:
    """Don't send us events caused by user errors"""
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, UserErrors):
            return None
    return event


if hasattr(sys, "_called_from_test") or VERSION == "dev":
    logger.debug("Not sending sentry cause we're in test or dev")
else:
    sentry_sdk.init(
        "https://aab05facf13049368d749e1b30a08b32@o511457.ingest.sentry.io/5610510",
        traces_sample_rate=1.0,
        integrations=[AtexitIntegration(at_exit_callback)],
        before_send=before_send,
    )
    sentry_sdk.set_user(
        {"email": GitConfigParser().get_value("user", "email", "no_user")}
    )
    sentry_sdk.set_tag("device_id", get_mac_address())
    sentry_sdk.set_tag("os_name", os.name)
    sentry_sdk.set_tag("platform", platform.system())
    sentry_sdk.set_tag("os_version", platform.version())
    sentry_sdk.set_tag("app_version", VERSION)
