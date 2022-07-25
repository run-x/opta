import os
import os.path

from pytest_mock import MockFixture

from opta.cleanup_files import cleanup_files
from opta.constants import TF_FILE_PATH


def test_cleanup() -> None:
    with open(TF_FILE_PATH, "w") as f:
        f.write("blah")
    cleanup_files()
    assert not os.path.exists(TF_FILE_PATH)


def test_at_exit_callback_without_pending(mocker: MockFixture) -> None:
    mocked_write = mocker.patch("opta.cli.sys.stderr.write")
    mocked_write.assert_not_called()
