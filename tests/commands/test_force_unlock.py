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
    mocker.patch("opta.commands.force_unlock.configure_kubectl")
    mocked_helm_list = mocker.patch(
        "opta.commands.force_unlock.Helm.get_helm_list",
        return_value=[
            {
                "name": "mocked-app",
                "namespace": "mocked-namespace",
                "revision": "1",
                "updated": "2021-09-23 19:55:15.503881027 +0000 UTC",
                "status": "pending-upgrade",
                "chart": "mocked-chart",
                "app_version": "mocked-version",
            }
        ],
    )
    mocked_rollback_helm = mocker.patch("opta.commands.force_unlock.Helm.rollback_helm")

    runner = CliRunner()
    result = runner.invoke(cli, ["force-unlock", "--config", FAKE_ENV_CONFIG])

    assert result.exit_code == 0
    mocked_click_confirm.assert_called_once_with(
        "This will remove the lock on the remote state."
        "\n\tPlease make sure that no other instance of opta command is running on this file."
        "\n\tDo you still want to proceed?",
        abort=True,
    )
    mocked_helm_list.assert_called_once_with(status="pending-upgrade")
    mocked_rollback_helm.assert_called_once_with(
        "mocked-app", namespace="mocked-namespace", revision="1"
    )


def test_force_unlock_env_no_rollback(mocker: MockFixture) -> None:
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
    mocker.patch("opta.commands.force_unlock.configure_kubectl")
    mocked_helm_list = mocker.patch(
        "opta.commands.force_unlock.Helm.get_helm_list", return_value=[],
    )
    mocked_rollback_helm = mocker.patch("opta.commands.force_unlock.Helm.rollback_helm")

    runner = CliRunner()
    result = runner.invoke(cli, ["force-unlock", "--config", FAKE_ENV_CONFIG])

    assert result.exit_code == 0
    mocked_click_confirm.assert_called_once_with(
        "This will remove the lock on the remote state."
        "\n\tPlease make sure that no other instance of opta command is running on this file."
        "\n\tDo you still want to proceed?",
        abort=True,
    )
    mocked_helm_list.assert_called_once_with(status="pending-upgrade")
    mocked_rollback_helm.assert_not_called()
