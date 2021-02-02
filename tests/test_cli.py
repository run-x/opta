import json
from typing import Any
from unittest.mock import call, mock_open, patch

import yaml
from pytest_mock import MockFixture, mocker  # noqa

from opta.cli import DEFAULT_GENERATED_TF_FILE, _apply


class TestCLI:
    def test_basic_apply(self, mocker: MockFixture) -> None:  # noqa
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
                    "modules": [
                        {
                            "core": {
                                "type": "aws-state-init",
                                "bucket_name": "{state_storage}",
                                "dynamodb_lock_table_name": "{state_storage}",
                            }
                        }
                    ],
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
