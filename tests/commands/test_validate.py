import os

from click.testing import CliRunner

from opta.cli import cli
from opta.exceptions import UserErrors

REGISTRY_URL = "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app"
TERRAFORM_OUTPUTS = {"docker_repo_url": REGISTRY_URL}


def test_validate_service() -> None:
    test_service_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "examples",
        "http-service",
        "opta.yaml",
    )
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", "-c", test_service_file_path, "--env", "aws-example"]
    )

    assert result.exit_code == 0


def test_validate_env() -> None:
    test_env_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "examples",
        "environments",
        "aws-env.yml",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_env_file_path])

    assert result.exit_code == 0


def test_wrong_type() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "org_name_wrong_type.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert result.exit_code == 1
    assert isinstance(result.exception, UserErrors)


def test_invalid_module_type() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "invalid_module_type.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert result.exit_code == 1
    assert isinstance(result.exception, UserErrors)
    assert "fake-module-type is not a valid module type" in result.exception.args[0]


def test_unexpected_field() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "unexpected_field.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert result.exit_code == 1
    assert isinstance(result.exception, UserErrors)
    assert "Unexpected element" in result.output


def test_unexpected_field_in_module() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "unexpected_module_field.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert result.exit_code == 1
    assert isinstance(result.exception, UserErrors)
    assert "Unexpected element" in result.output
