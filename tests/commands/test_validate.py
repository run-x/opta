import os

from click.testing import CliRunner

from opta.cli import cli

REGISTRY_URL = "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app"
TERRAFORM_OUTPUTS = {"docker_repo_url": REGISTRY_URL}


def test_validate_service() -> None:
    test_service_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "new_service", "opta.yml"
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_service_file_path])

    assert result.exit_code == 0


def test_validate_env() -> None:
    test_env_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "new_env", "opta.yml"
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_env_file_path])

    assert result.exit_code == 0
