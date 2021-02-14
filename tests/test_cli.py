import json
import os
import os.path
from typing import Any
from unittest.mock import call, mock_open, patch

import yaml
from pytest_mock import MockFixture

from opta.cli import TERRAFORM_PLAN_FILE_PATH, _cleanup, at_exit_callback
from opta.constants import TF_FILE_PATH
from opta.core.generator import gen
from tests.fixtures.apply import APPLY_WITHOUT_ORG_ID, BASIC_APPLY


class TestCLI:
    def test_cleanup(self) -> None:
        with open(TF_FILE_PATH, "w") as f:
            f.write("blah")
        with open(TERRAFORM_PLAN_FILE_PATH, "w") as f:
            f.write("blah")
        _cleanup()
        assert not os.path.exists(TF_FILE_PATH)
        assert not os.path.exists(TERRAFORM_PLAN_FILE_PATH)

    def test_at_exit_callback_with_pending(self, mocker: MockFixture) -> None:
        mocked_write = mocker.patch("opta.cli.sys.stderr.write")
        mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
        at_exit_callback(1, 1)
        mocked_write.assert_has_calls(
            [call(mocker.ANY), call(mocker.ANY), call(mocker.ANY)]
        )
        mocked_flush.assert_called_once_with()

    def test_at_exit_callback_without_pending(self, mocker: MockFixture) -> None:
        mocked_write = mocker.patch("opta.cli.sys.stderr.write")
        mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
        at_exit_callback(0, 1)
        mocked_write.assert_not_called()
        mocked_flush.assert_called_once_with()

    def test_basic_apply(self, mocker: MockFixture) -> None:
        mocked_exists = mocker.patch("os.path.exists")
        mocked_exists.return_value = True
        test_cases: Any = [BASIC_APPLY, APPLY_WITHOUT_ORG_ID]

        for (i, o) in test_cases:
            old_open = open
            write_open = mock_open()

            def new_open(a: str, b: Any = "r") -> Any:
                if a == "opta.yml":
                    return mock_open(read_data=yaml.dump(i)).return_value
                elif a == TF_FILE_PATH:
                    return write_open.return_value
                else:
                    return old_open(a, b)

            with patch("builtins.open") as mocked_open:
                mocked_open.side_effect = new_open

                gen("opta.yml", None)

                write_open().write.assert_called_once_with(json.dumps(o, indent=2))
