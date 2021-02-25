from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli


def test_deploy_basic(mocker: MockFixture) -> None:
    mock_push = mocker.patch("opta.commands.deploy.push")
    mock_apply = mocker.patch("opta.commands.deploy.apply")
    runner = CliRunner()
    result = runner.invoke(cli, ["deploy", "local_image:local_tag"])

    assert result.exit_code == 0
    mock_push.assert_called_once_with(
        image="local_image:local_tag", config="opta.yml", env=None, tag=None
    )
    mock_apply.assert_called_once_with(
        config="opta.yml",
        env=None,
        refresh=False,
        max_module=None,
        image_tag="local_tag",
        test=False,
    )


def test_deploy_all_flags(mocker: MockFixture) -> None:
    mock_push = mocker.patch("opta.commands.deploy.push")
    mock_apply = mocker.patch("opta.commands.deploy.apply")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "deploy",
            "local_image:local_tag",
            "--config",
            "app/opta.yml",
            "--env",
            "staging",
            "--tag",
            "latest",
        ],
    )

    assert result.exit_code == 0
    mock_push.assert_called_once_with(
        image="local_image:local_tag", config="app/opta.yml", env="staging", tag="latest"
    )
    mock_apply.assert_called_once_with(
        config="app/opta.yml",
        env="staging",
        refresh=False,
        max_module=None,
        image_tag="latest",
        test=False,
    )
