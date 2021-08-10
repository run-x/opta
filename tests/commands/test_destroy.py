import os

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.destroy import destroy
from tests.utils import get_call_args

FAKE_ENV_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "module_processors",
    "dummy_config_parent.yaml",
)

FAKE_SERVICE_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "module_processors", "dummy_config1.yaml",
)


def test_destroy_env_with_children(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.destroy_all")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=["a", "b"],
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    print(result.exception)
    assert result.exit_code == 1

    assert not mocked_gen_all.called


def test_destroy_env_without_children(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.destroy_all")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    print(result.exception)
    assert result.exit_code == 0

    args = get_call_args(mocked_gen_all)

    assert len(args) == 1
    assert args[0].name == "dummy-parent"


def test_destroy_service(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.destroy_all")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_SERVICE_CONFIG])

    print(result.exception)
    assert result.exit_code == 0

    args = get_call_args(mocked_gen_all)

    assert len(args) == 1
    assert args[0].name == "dummy-config-1"
