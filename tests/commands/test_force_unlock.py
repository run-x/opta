import os

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli
from opta.layer import Layer

FAKE_ENV_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "module_processors",
    "dummy_config_parent.yaml",
)


def test_force_unlock_env_with_force_terraform(mocker: MockFixture) -> None:
    mocked_click = mocker.patch("opta.commands.apply.click")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mocked_layer = mocker.Mock(spec=Layer)
    mocker.patch(
        "opta.commands.force_unlock.Layer.load_from_yaml", return_value=mocked_layer
    )
    mocker.patch("opta.commands.force_unlock.amplitude_client.send_event")
    mocker.patch(
        "opta.commands.force_unlock.Layer.verify_cloud_credentials", return_value=None
    )
    mocker.patch("opta.commands.force_unlock.gen_all")
    mocker.patch("opta.commands.force_unlock.Terraform.init")
    mocker.patch("opta.commands.force_unlock.Terraform.force_unlock")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["force-unlock", "--config", FAKE_ENV_CONFIG, "--force-terraform"]
    )

    print(result.exception)
    assert result.exit_code == 0
    mocked_click.assert_not_called()


def test_force_unlock_env(mocker: MockFixture) -> None:
    mocked_click_confirm = mocker.patch(
        "opta.commands.apply.click.confirm", return_value="y"
    )
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mocked_layer = mocker.Mock(spec=Layer)
    mocker.patch(
        "opta.commands.force_unlock.Layer.load_from_yaml", return_value=mocked_layer
    )
    mocker.patch("opta.commands.force_unlock.amplitude_client.send_event")
    mocker.patch(
        "opta.commands.force_unlock.Layer.verify_cloud_credentials", return_value=None
    )
    mocker.patch("opta.commands.force_unlock.gen_all")
    mocker.patch("opta.commands.force_unlock.Terraform.init")
    mocker.patch("opta.commands.force_unlock.Terraform.force_unlock")

    runner = CliRunner()
    result = runner.invoke(cli, ["force-unlock", "--config", FAKE_ENV_CONFIG])

    print(result.exception)
    assert result.exit_code == 0
    mocked_click_confirm.assert_called_once_with(
        "Do you really want to force-unlock?"
        "\t\nTerraform will remove the lock on the remote state."
        "\t\nThis will allow local Terraform commands to modify this state, even though it may be still be in use.",
        abort=True,
    )
