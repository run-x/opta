import logging
import os
import signal
import sys
import tempfile
from asyncio import TimeoutError
from subprocess import (  # nosec
    PIPE,
    CalledProcessError,
    CompletedProcess,
    Popen,
    TimeoutExpired,
)
from traceback import format_exc
from typing import Optional, Union

import psutil

try:
    import _winapi  # noqa

    _mswindows = True
except ModuleNotFoundError:
    _mswindows = False


from opta.constants import DEV_VERSION, VERSION
from opta.utils import ansi_scrub
from opta.utils.runtee import run  # type: ignore

# Logging setup for nice subprocess
nice_logger = logging.getLogger(__name__)
nice_logger.setLevel(logging.DEBUG)
nice_logger.propagate = False


def log_to_datadog(msg: str, severity: str) -> None:
    try:
        msg = ansi_scrub(msg)
        if hasattr(sys, "_called_from_test") or VERSION == DEV_VERSION or not VERSION:
            if os.environ.get("OPTA_DEBUG", "") == "DATADOG_LOCAL":
                print(">>>>>>>>>>>>>>>>>>>>Datadog log start")
                print(msg)
                print("<<<<<<<<<<<<<<<<<<<<Datadog log end")

        if severity == "ERROR":
            nice_logger.error(msg)
        else:
            nice_logger.info(msg)
    except:  # nosec   # noqa: E722
        # Logging error to datadog SaaS, happens,
        # not the end of world, silently fail
        pass


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
    use_asyncio_nice_run=False,
    **kwargs,
) -> CompletedProcess:

    if (
        use_asyncio_nice_run is False
    ):  # Just use the original blocking Popen, this doesn't log subprocess output to datadog
        if input is not None:
            if kwargs.get("stdin") is not None:
                raise ValueError("stdin and input arguments may not both be used.")
            kwargs["stdin"] = PIPE

        if capture_output:
            if kwargs.get("stdout") is not None or kwargs.get("stderr") is not None:
                raise ValueError(
                    "stdout and stderr arguments may not be used " "with capture_output."
                )
            kwargs["stdout"] = PIPE
            kwargs["stderr"] = PIPE

        with Popen(*popenargs, **kwargs) as process:
            try:
                stdout, stderr = process.communicate(input, timeout=timeout)
            except TimeoutExpired as exc:
                process.send_signal(signal.SIGINT)
                # Wait again, now that the child has received SIGINT, too.
                process.wait(timeout=exit_timeout)
                process.kill()
                if _mswindows:
                    # Windows accumulates the output in a single blocking
                    # read() call run on child threads, with the timeout
                    # being done in a join() on those threads.  communicate()
                    # _after_ kill() is required to collect that and add it
                    # to the exception.
                    exc.stdout, exc.stderr = process.communicate()
                else:
                    # POSIX _communicate already populated the output so
                    # far into the TimeoutExpired exception.
                    process.wait()
                raise
            except KeyboardInterrupt:
                print("Received keyboard interrupt")
                # Wait again, now that the child has received SIGINT, too.
                process.wait(timeout=exit_timeout)
                raise
            except Exception:  # Including KeyboardInterrupt, communicate handled that.
                process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            retcode = process.poll()
            if check and retcode:
                raise CalledProcessError(
                    retcode, process.args, output=stdout, stderr=stderr
                )
        if type(stdout) is bytes:
            stdout = stdout.decode("utf-8")
        if type(stderr) is bytes:
            stderr = stderr.decode("utf-8")
        return CompletedProcess(process.args, retcode or 0, stdout, stderr)
    else:
        try:
            listargs = list(popenargs)
            listargs[0].insert(0, "exec")
            popenargs = tuple(listargs)
            log_to_datadog(
                "Calling subprocess with these arguments:\n" + " ".join(*popenargs),
                "INFO",
            )

            with tempfile.TemporaryFile() as f:
                if input:
                    f.write(input)  # type: ignore
                    f.seek(0)
                    result = run(
                        *popenargs,
                        input=f,
                        timeout=timeout,
                        check=check,
                        tee=tee,
                        capture_output=capture_output,
                        **kwargs,
                    )
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
            log_to_datadog(
                "SUBPROCESS TIMEOUT EXCEPTION\n{}".format(format_exc()), "ERROR"
            )
            raise exc

        except KeyboardInterrupt:
            print("Received keyboard interrupt")
            log_to_datadog(
                "SUBPROCESS KEYBOARDINTERRUPT EXCEPTION\n{}".format(format_exc()), "ERROR"
            )
            raise
        except CalledProcessError as e:
            log_to_datadog(
                "SUBPROCESS CALLEDPROCESSERROR\n STDOUT:{}".format(e.stdout), "ERROR"
            )
            stderr_lines = "SUBPROCESS CALLEDPROCESSERROR\n STDERR:{}".format(e.stderr)
            for line in stderr_lines.split("\n"):
                log_to_datadog(line, "ERROR")
            raise e
        except Exception as e:  # Including KeyboardInterrupt, communicate handled that.
            log_to_datadog("SUBPROCESS OTHER EXCEPTION\n{}".format(format_exc()), "ERROR")
            raise e

        log_to_datadog(
            "SUBPROCESS NORMAL RUN\nSTDOUT:\n{}\n".format(result.stdout), "INFO",
        )
        return result
