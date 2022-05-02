from datetime import datetime

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.show import config
from opta.layer import StructuredConfig


def test_show_config(mocker: MockFixture) -> None:
    mock_bucket = "test-bucket"
    mock_config = "test-config"
    mock_yaml_config = "test-yaml-config"
    structured_config: StructuredConfig = {
        "opta_version": "dev",
        "date": datetime.utcnow().isoformat(),
        "original_spec": mock_yaml_config,
        "defaults": {},
    }

    mock_logger = mocker.patch("opta.commands.show.logger")
    mocker.patch(
        "opta.commands.show.AWS.get_all_remote_configs",
        return_value={mock_bucket: {mock_config: structured_config}},
    )
    runner = CliRunner()
    result = runner.invoke(config, ["--cloud", "aws"])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once_with(
        f"# Bucket Name: {mock_bucket}\n# Config Name: {mock_config}\n{mock_yaml_config}\n"
    )
