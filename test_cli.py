import json
from typing import Any
from unittest.mock import mock_open, patch

import yaml

from opta.cli import _gen


@patch("os.path.exists")
def test_basic_gen(_: Any) -> None:
    test_cases: Any = [
        (
            {
                "meta": {
                    "create-env": "dev1",
                    "name": "dev1",
                    "providers": {
                        "google": {"project": "xyz", "region": "xyz", "zone": "xyz"}
                    },
                },
                "modules": [
                    {"core": {"type": "state-init", "bucket_name": "{state_storage}"}}
                ],
            },
            {
                "provider": {
                    "google": {"project": "xyz", "region": "xyz", "zone": "xyz"}
                },
                "terraform": {
                    "backend": {"gcs": {"bucket": "opta-tf-state-dev1", "prefix": "dev1"}}
                },
                "module": {
                    "core": {
                        "source": "git@github.com:run-x/runxc-tf-modules.git//state-init",
                        "bucket_name": "opta-tf-state-dev1",
                    }
                },
                "output": {
                    "state-bucket-name": {"value": "${module.core.state-bucket-name }"}
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
            elif a == "main.tf.json":
                return write_open.return_value
            else:
                return old_open(a, b)

        with patch("builtins.open") as mocked_open:
            mocked_open.side_effect = new_open

            _gen("opta.yml", "main.tf.json", True, False)

            write_open().write.assert_called_once_with(json.dumps(o, indent=2))
