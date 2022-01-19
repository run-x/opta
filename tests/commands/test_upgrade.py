from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli
from opta.commands.upgrade import TEMP_INSTALLATION_FILENAME


def test_upgrade(mocker: MockFixture) -> None:
    mock_check_version_upgrade = mocker.patch(
        "opta.commands.upgrade.check_version_upgrade"
    )
    mock_check_version_upgrade.return_value = True
    mock_make_installation_file = mocker.patch(
        "opta.commands.upgrade._make_installation_file"
    )
    mock_upgrade_successful = mocker.patch("opta.commands.upgrade._upgrade_successful")
    mock_cleanup_installation_file = mocker.patch(
        "opta.commands.upgrade._cleanup_installation_file"
    )
    mock_nice_run = mocker.patch("opta.commands.upgrade.nice_run")

    runner = CliRunner()
    result = runner.invoke(cli, ["upgrade"])
    assert result.exit_code == 0
    mock_check_version_upgrade.assert_called_once_with(is_upgrade_call=True)
    mock_make_installation_file.assert_called_once()
    mock_nice_run.assert_called_once_with([f"./{TEMP_INSTALLATION_FILENAME}"], input=b"y")
    mock_upgrade_successful.assert_called_once()
    mock_cleanup_installation_file.assert_called_once()
