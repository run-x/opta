import logging
import os
import signal
import sys
from asyncio import TimeoutError
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess  # nosec
from traceback import format_exc
from typing import Optional, Union

import psutil

from opta.constants import DEV_VERSION, VERSION
from opta.datadog_logging import DatadogLogHandler
from opta.utils import ansi_scrub
from opta.utils.runtee import run  # type: ignore

# Datadog logging setup for nice subprocess
dd_handler = DatadogLogHandler()
nice_logger = logging.getLogger(__name__)
nice_logger.setLevel(logging.DEBUG)
nice_logger.addHandler(dd_handler)
nice_logger.propagate = False


def log_to_datadog(msg: str, severity: str) -> None:
    msg = ansi_scrub(msg)
    if hasattr(sys, "_called_from_test") or VERSION == DEV_VERSION or not VERSION:
        print("Not logging to Datadog as this appears to be a dev/test version of opta")
        print("Would have logged this string to DD:\n")
        print(">>>>>>>>>>>>>>>>>>>>Datadog log start")
        print(msg)
        print("<<<<<<<<<<<<<<<<<<<<Datadog log end")
        dd_handler.setLevel(logging.CRITICAL)

    if severity == "ERROR":
        nice_logger.error(msg)
    else:
        nice_logger.info(msg)


def signal_all_child_processes(sig: int = signal.SIGINT) -> None:
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        print(child.pid)
        os.kill(child.pid, sig)


def nice_run(  # type: ignore # nosec
    *popenargs,
    input: Optional[Union[str, bytes]] = None,
    capture_output: bool = False,
    timeout: Optional[float] = None,
    exit_timeout: Optional[float] = None,
    tee: bool = True,
    check: bool = False,
    **kwargs,
) -> CompletedProcess:

    try:
        Path("/tmp/optainput.tmp").touch()
        listargs = list(popenargs)
        listargs[0].insert(0, "exec")
        popenargs = tuple(listargs)
        log_to_datadog(
            "Calling subprocess with these arguments:\n" + " ".join(*popenargs), "INFO"
        )
        if input:
            with open("/tmp/optainput.tmp", "wb") as f:
                f.write(input)  # type: ignore
            result = run(
                *popenargs,
                input=open("/tmp/optainput.tmp", "rb"),
                timeout=timeout,
                check=check,
                tee=tee,
                capture_output=capture_output,
                **kwargs,
            )
            os.remove("/tmp/optainput.tmp")
        else:
            result = run(
                *popenargs,
                timeout=timeout,
                check=check,
                tee=tee,
                capture_output=capture_output,
                **kwargs,
            )

    except TimeoutError as exc:
        print("Timeout while running command")
        signal_all_child_processes()
        log_to_datadog("SUBPROCESS TIMEOUT EXCEPTION\n{}".format(format_exc()), "ERROR")
        raise exc

    except KeyboardInterrupt as k:
        print("Received keyboard interrupt")
        log_to_datadog(
            "SUBPROCESS KEYBOARDINTERRUPT EXCEPTION\n{}".format(format_exc()), "ERROR"
        )
        raise k
    except CalledProcessError as e:
        log_to_datadog(
            "SUBPROCESS CALLEDPROCESSERROR\n STDOUT:\n{}\nSTDERR:\n{}\n".format(
                e.stdout, e.stderr
            ),
            "ERROR",
        )
        raise e
    except Exception as e:  # Including KeyboardInterrupt, communicate handled that.
        log_to_datadog("SUBPROCESS OTHER EXCEPTION\n{}".format(format_exc()), "ERROR")
        raise e

    log_to_datadog(
        "SUBPROCESS NORMAL RUN\nSTDOUT:\n{}\n".format(result.stdout), "INFO",
    )
    return result
