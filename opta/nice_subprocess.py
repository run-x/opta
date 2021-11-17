import signal
from subprocess import (  # nosec
    PIPE,
    CalledProcessError,
    CompletedProcess,
    TimeoutExpired,
    DEVNULL
)
from typing import Optional, Union
from subprocess_tee import run

try:
    import _winapi  # noqa

    _mswindows = True
except ModuleNotFoundError:
    _mswindows = False


def nice_run(  # type: ignore # nosec
    *popenargs,
    input: Optional[Union[str, bytes]] = None,
    capture_output: bool = False,
    timeout: Optional[float] = None,
    exit_timeout: Optional[float] = None,
    check: bool = False,
    **kwargs,
) -> CompletedProcess:

    try:
        result = run(*popenargs, input=input, timeout=timeout, check=check, capture_output=capture_output, **kwargs)
    except TimeoutExpired as exc:
        print("Timeout while running command")
        raise exc
    except KeyboardInterrupt as k:
        print("Received keyboard interrupt")
        # Wait again, now that the child has received SIGINT, too.
        raise k
    except CalledProcessError as e:
        raise e
    except Exception:  # Including KeyboardInterrupt, communicate handled that.
        raise
    return result

# def nice_run(  # type: ignore # nosec
#     *popenargs,
#     input: Optional[Union[str, bytes]] = None,
#     capture_output: bool = False,
#     timeout: Optional[float] = None,
#     exit_timeout: Optional[float] = None,
#     check: bool = False,
#     **kwargs,
# ) -> CompletedProcess:
#     """Run command with arguments and return a CompletedProcess instance.

#     The returned instance will have attributes args, returncode, stdout and
#     stderr. By default, stdout and stderr are not captured, and those attributes
#     will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them.

#     If check is True and the exit code was non-zero, it raises a
#     CalledProcessError. The CalledProcessError object will have the return code
#     in the returncode attribute, and output & stderr attributes if those streams
#     were captured.

#     If timeout is given, and the process takes too long, a TimeoutExpired
#     exception will be raised.

#     There is an optional argument "input", allowing you to
#     pass bytes or a string to the subprocess's stdin.  If you use this argument
#     you may not also use the Popen constructor's "stdin" argument, as
#     it will be used internally.

#     By default, all communication is in bytes, and therefore any "input" should
#     be bytes, and the stdout and stderr will be bytes. If in text mode, any
#     "input" should be a string, and stdout and stderr will be strings decoded
#     according to locale encoding, or by "encoding" if set. Text mode is
#     triggered by setting any of text, encoding, errors or universal_newlines.

#     The other arguments are the same as for the Popen constructor.
#     """
#     if input is not None:
#         if kwargs.get("stdin") is not None:
#             raise ValueError("stdin and input arguments may not both be used.")
#         kwargs["stdin"] = PIPE

#     if capture_output:
#         if kwargs.get("stdout") is not None or kwargs.get("stderr") is not None:
#             raise ValueError(
#                 "stdout and stderr arguments may not be used " "with capture_output."
#             )
#         kwargs["stdout"] = PIPE
#         kwargs["stderr"] = PIPE

#     with Popen(*popenargs, **kwargs) as process:
#         try:
#             stdout, stderr = process.communicate(input, timeout=timeout)
#             for line in iter(process.stderr.readline, b''):
#                 print (line),
#                 process.stdout.close()
#                 process.wait()
#             for line in iter(process.stdout.readline, b''):
#                 print (line),
#                 process.stdout.close()
#                 process.wait()


#         except TimeoutExpired as exc:
#             process.send_signal(signal.SIGINT)
#             # Wait again, now that the child has received SIGINT, too.
#             process.wait(timeout=exit_timeout)
#             process.kill()
#             if _mswindows:
#                 # Windows accumulates the output in a single blocking
#                 # read() call run on child threads, with the timeout
#                 # being done in a join() on those threads.  communicate()
#                 # _after_ kill() is required to collect that and add it
#                 # to the exception.
#                 exc.stdout, exc.stderr = process.communicate()
#             else:
#                 # POSIX _communicate already populated the output so
#                 # far into the TimeoutExpired exception.
#                 process.wait()
#             raise
#         except KeyboardInterrupt:
#             print("Received keyboard interrupt")
#             # Wait again, now that the child has received SIGINT, too.
#             process.wait(timeout=exit_timeout)
#             raise
#         except Exception:  # Including KeyboardInterrupt, communicate handled that.
#             process.kill()
#             # We don't call process.wait() as .__exit__ does that for us.
#             raise
#         retcode = process.poll()
#         if check and retcode:
#             raise CalledProcessError(retcode, process.args, output=stdout, stderr=stderr)
#     return CompletedProcess(process.args, retcode or 0, stdout, stderr)
