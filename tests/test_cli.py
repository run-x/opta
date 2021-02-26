import os
import os.path
from unittest.mock import call

from pytest_mock import MockFixture

from opta.cli import _cleanup
from opta.constants import TF_FILE_PATH
from opta.sentry import at_exit_callback


def test_cleanup() -> None:
    with open(TF_FILE_PATH, "w") as f:
        f.write("blah")
    _cleanup()
    assert not os.path.exists(TF_FILE_PATH)


def test_at_exit_callback_with_pending(mocker: MockFixture) -> None:
    mocked_write = mocker.patch("opta.cli.sys.stderr.write")
    mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
    at_exit_callback(1, 1)
    mocked_write.assert_has_calls([call(mocker.ANY), call(mocker.ANY), call(mocker.ANY)])
    mocked_flush.assert_called_once_with()


def test_at_exit_callback_without_pending(mocker: MockFixture) -> None:
    mocked_write = mocker.patch("opta.cli.sys.stderr.write")
    mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
    at_exit_callback(0, 1)
    mocked_write.assert_not_called()
    mocked_flush.assert_called_once_with()
