import json
import os
from typing import Any
from unittest.mock import call, mock_open, patch

import yaml
from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import (
    DEFAULT_GENERATED_TF_FILE,
    TERRAFORM_PLAN_FILE,
    _apply,
    _cleanup,
    at_exit_callback,
    output,
)


class TestCLI:
    def test_cleanup(self) -> None:
        with open(DEFAULT_GENERATED_TF_FILE, "w") as f:
            f.write("blah")
        with open(TERRAFORM_PLAN_FILE, "w") as f:
            f.write("blah")
        _cleanup()
        assert not os.path.exists(DEFAULT_GENERATED_TF_FILE)
        assert not os.path.exists(TERRAFORM_PLAN_FILE)

    def test_output(self, mocker: MockFixture) -> None:
        mocker.patch("opta.cli.os.remove")
        mocked_apply = mocker.patch("opta.cli.apply")
        mocked_shell_cmds = mocker.patch("opta.cli.nice_run")

        runner = CliRunner()
        result = runner.invoke(output, [])
        assert result.exit_code == 0
        assert mocked_apply.call_count == 1
        assert mocked_shell_cmds.call_count == 3

        # Don't run terraform init if .terraform/ exists.
        os.mkdir(".terraform")
        mocked_shell_cmds.call_count = 0

        result = runner.invoke(output)
        assert result.exit_code == 0
        assert mocked_shell_cmds.call_count == 2

        # Clean up
        os.rmdir(".terraform")

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
        test_cases: Any = [
            (
                {
                    "meta": {
                        "create-env": "dev1",
                        "name": "dev1",
                        "providers": {
                            "aws": {"allowed_account_ids": ["abc"], "region": "us-east-1"}
                        },
                    },
                    "modules": {
                        "core": {
                            "type": "aws-state-init",
                            "bucket_name": "{state_storage}",
                            "dynamodb_lock_table_name": "{state_storage}",
                        }
                    },
                },
                {
                    "provider": {
                        "aws": {"allowed_account_ids": ["abc"], "region": "us-east-1"}
                    },
                    "terraform": {
                        "backend": {
                            "s3": {
                                "bucket": "opta-tf-state-dev1",
                                "key": "dev1",
                                "dynamodb_table": "opta-tf-state-dev1",
                                "region": "us-east-1",
                            }
                        }
                    },
                    "module": {
                        "core": {
                            "source": "./config/tf_modules/aws-state-init",
                            "bucket_name": "opta-tf-state-dev1",
                            "dynamodb_lock_table_name": "opta-tf-state-dev1",
                        }
                    },
                    "output": {
                        "state_bucket_id": {"value": "${module.core.state_bucket_id }"},
                        "state_bucket_arn": {"value": "${module.core.state_bucket_arn }"},
                        "kms_account_key_arn": {
                            "value": "${module.core.kms_account_key_arn }"
                        },
                        "kms_account_key_id": {
                            "value": "${module.core.kms_account_key_id }"
                        },
                    },
                },
            )
        ]

        for (i, o) in test_cases:
            old_open = open
            write_open = mock_open()

            def new_open(a: str, b: Any = "r") -> Any:
                if a == "opta.yml":
                    return mock_open(read_data=yaml.dump(i)).return_value
                elif a == DEFAULT_GENERATED_TF_FILE:
                    return write_open.return_value
                else:
                    return old_open(a, b)

            with patch("builtins.open") as mocked_open:
                mocked_open.side_effect = new_open

                _apply("opta.yml", DEFAULT_GENERATED_TF_FILE, None, True, False, None, [])

                mocked_exists.assert_has_calls(
                    [
                        call("opta.yml"),
                        call(mocker.ANY),
                        call(mocker.ANY),
                        call(mocker.ANY),
                        call(mocker.ANY),
                        call(mocker.ANY),
                    ],
                    any_order=True,
                )

                write_open().write.assert_called_once_with(json.dumps(o, indent=2))
