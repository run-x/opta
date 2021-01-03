import json
from typing import Any
from unittest.mock import mock_open, patch

import yaml
from click.testing import CliRunner

from opta.cli import cli


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
                "core": {"type": "init"},
            },
            {
                "provider": {
                    "google": {"project": "xyz", "region": "xyz", "zone": "xyz"}
                },
                "terraform": {
                    "backend": {"gcs": {"bucket": "opta_tf_state_dev1", "prefix": "env"}}
                },
                "resource": {
                    "google_storage_bucket": {
                        "tf_state": {
                            "name": "opta_tf_state_dev1",
                            "versioning": {"enabled": True},
                        }
                    }
                },
                "module": {
                    "core": {
                        "source": "git@github.com:run-x/runxc-tf-modules.git//init",
                        "name": "dev1-core",
                    }
                },
                "output": {
                    "gcp-network": {"value": "${module.core.gcp-network}"},
                    "k8s-cluster": {"value": "${module.core.k8s-cluster}"},
                },
            },
        )
    ]

    for (i, o) in test_cases:
        old_open = open
        write_open = mock_open()

        def new_open(a: str, b: Any = None) -> Any:
            if a == "opta.yml":
                return mock_open(read_data=yaml.dump(i)).return_value
            elif a == "main.tf.json":
                return write_open.return_value
            else:
                return old_open(a, b)

        with patch("builtins.open") as mocked_open:
            mocked_open.side_effect = new_open
            CliRunner().invoke(cli, ["gen"])

            write_open().write.assert_called_once_with(json.dumps(o, indent=2))
