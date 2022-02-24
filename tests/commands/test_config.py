from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.config import view


def test_config_view(mocker: MockFixture) -> None:
    mock_bucket = "test-bucket"
    mock_config = "test-config"
    mock_yaml_config = "test-yaml-config"
    mock_logger = mocker.patch("opta.commands.config.logger")
    mocker.patch(
        "opta.commands.config.AWS.get_detailed_config_map",
        return_value={mock_bucket: {mock_config: mock_yaml_config}},
    )
    runner = CliRunner()
    result = runner.invoke(view, ["--cloud", "aws"])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once_with(
        f"# Bucket Name: {mock_bucket}\n# Config Name: {mock_config}\n{mock_yaml_config}\n\n"
    )
