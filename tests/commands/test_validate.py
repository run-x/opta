import os

from click.testing import CliRunner
from yamale.yamale_error import YamaleError

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


def test_wrong_type() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "org_name_wrong_type.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert isinstance(result.exception, YamaleError)

    results = result.exception.results
    assert len(results) == 1
    assert "org_name: '1' is not a str." in results[0].errors[0]


def test_invalid_module_type() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "invalid_module_type.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert isinstance(result.exception, YamaleError)

    results = result.exception.results
    assert len(results) == 1
    assert "fake-module-type is not a valid module type" in results[0].errors[0]


def test_unexpected_field() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "unexpected_field.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert isinstance(result.exception, YamaleError)

    results = result.exception.results
    assert len(results) == 1
    assert "Unexpected element" in results[0].errors[0]


def test_unexpected_field_in_module() -> None:
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "sample_opta_files",
        "unexpected_module_field.yaml",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-c", test_file])
    assert isinstance(result.exception, YamaleError)

    results = result.exception.results
    assert len(results) == 1
    assert "Unexpected element" in results[0].errors[0]
