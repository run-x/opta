# type: ignore
import os
from subprocess import TimeoutExpired

import pytest

from opta.nice_subprocess import nice_run

GRACEFUL_TERMINATION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "tests", "signal_gracefully_terminated",
)
SIGNAL_HANDLER_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "tests", "signal_handler.py",
)


class TestNiceRun:
    def test_echo(self):
        completed_process = nice_run(
            ["echo", "Hello world!"], check=True, capture_output=True
        )
        assert completed_process.returncode == 0
        assert completed_process.stdout == "Hello world!\n"

    def test_timeout(self):
        with pytest.raises(TimeoutExpired):
            nice_run(["sleep", "5"], check=True, capture_output=True, timeout=1)

    def test_graceful_timeout_exit(self):
        if os.path.exists(GRACEFUL_TERMINATION_FILE):
            os.remove(GRACEFUL_TERMINATION_FILE)

        with pytest.raises(TimeoutExpired):
            nice_run(["python", SIGNAL_HANDLER_SCRIPT], timeout=3)

        assert os.path.exists(GRACEFUL_TERMINATION_FILE)

        # clean up
        os.remove(GRACEFUL_TERMINATION_FILE)
