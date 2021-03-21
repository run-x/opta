import os
from typing import Any, List
from unittest.mock import MagicMock

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.destroy import destroy

FAKE_ENV_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "module_processors",
    "dummy_config_parent.yaml",
)

FAKE_SERVICE_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "module_processors", "dummy_config1.yaml",
)


def test_destroy(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.destroy_all")

    mocker.patch(
        "opta.commands.destroy._download_all_opta_configs",
        return_value=[FAKE_ENV_CONFIG, FAKE_SERVICE_CONFIG],
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    print(result.exception)
    assert result.exit_code == 0

    actual_destroy_order = [layer.name for layer in get_call_args(mocked_gen_all)]
    assert actual_destroy_order == ["dummy-config-1", "dummy-parent"]


def get_call_args(mocked_obj: MagicMock) -> List[Any]:
    raw_call_args = mocked_obj.call_args_list
    return [arg[0][0] for arg in raw_call_args]
