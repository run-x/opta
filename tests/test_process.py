import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli
from opta.core.terraform2.terraform_file import TerraformFile
from opta.utils import features


@pytest.fixture
def env_path() -> str:
    path = os.path.join(
        os.path.dirname(__file__), "fixtures", "sample_opta_files", "module_api_test.yaml"
    )

    assert os.path.exists(path)

    return path


@pytest.fixture(autouse=True)
def run_before_and_after_tests(mocker: MockFixture) -> Generator:
    """Fixture to execute asserts before and after a test is run"""

    # no actual kubernetes/cloud needed
    no_calls = [
        "boto3.client",
        "opta.core.kubernetes.load_kube_config",
        "opta.core.kubernetes.set_kube_config",
    ]

    mocked_no_calls = [mocker.patch(target) for target in no_calls]

    yield

    for mocked in mocked_no_calls:
        mocked.assert_not_called()


@pytest.fixture(autouse=True)
def enable_module_api() -> Generator:
    old = os.environ.get(features._FEATURE_MODULE_API_ENV)
    os.environ[features._FEATURE_MODULE_API_ENV] = "1"
    features._check_env.cache_clear()

    assert features.is_module_api_enabled()

    yield

    if old is None:
        del os.environ[features._FEATURE_MODULE_API_ENV]
    else:
        os.environ[features._FEATURE_MODULE_API_ENV] = old

    features._check_env.cache_clear()


@dataclass
class MockedTerraform:
    apply: MagicMock
    download_state: MagicMock
    ensure_local_state_dir: MagicMock
    nice_run: MagicMock
    plan: MagicMock
    upload_state: MagicMock


@pytest.fixture(autouse=True)
def tf_mocks(mocker: MockFixture) -> Generator[MockedTerraform, None, None]:
    module = "opta.core.terraform2.terraform"
    tf = f"{module}.Terraform"

    patch_targets = [
        "apply",
        "download_state",
        "ensure_local_state_dir",
        "plan",
        "upload_state",
    ]

    patches = {
        target: mocker.patch(f"{tf}.{target}", return_value=None)
        for target in patch_targets
    }

    # Special return values
    patches["download_state"].return_value = False

    # Extra patches
    patches["nice_run"] = mocker.patch(f"{module}.nice_run", return_value=None)

    mocked_copyfile = mocker.patch(f"{module}.copyfile", return_value=None)

    yield MockedTerraform(**patches)

    mocked_copyfile.assert_not_called()


@pytest.fixture(autouse=True)
def temp_workdir(tmp_path: Path) -> Generator:
    cwd = os.getcwd()

    os.chdir(tmp_path)

    yield

    os.chdir(cwd)


class TestApply:
    def test_apply(
        self, env_path: str, tf_mocks: MockedTerraform, mocker: MockFixture
    ) -> None:
        mocker.patch("opta.commands.apply.opta_acquire_lock")
        mocker.patch("opta.commands.apply.opta_release_lock")
        mocked_logger = mocker.patch("opta.process.logger")
        mocked_warning: MagicMock = mocked_logger.warning
        mocked_displayer = mocker.patch("opta.core.plan_displayer.PlanDisplayer.display")
        mocked_write = mocker.patch("opta.process.write_tf", return_value=None)

        runner = CliRunner()
        result = runner.invoke(cli, ["apply", "-c", env_path, "--auto-approve"])

        assert result.exit_code == 0

        tf_mocks.ensure_local_state_dir.assert_called_once()
        tf_mocks.plan.assert_called_once()
        tf_mocks.apply.assert_called_once_with(
            auto_approve=True, plan="tf.plan", quiet=False
        )
        tf_mocks.upload_state.assert_called_once()

        mocked_warning.assert_called_once_with(
            "Opta's module API mode is in preview and is NOT READY FOR PRODUCTION USE."
        )
        mocked_displayer.assert_called_once()

        mocked_write.assert_called_once()
        mocked_write_args = mocked_write.call_args.args[0]
        assert isinstance(mocked_write_args, TerraformFile)

        expected_tf_file = TerraformFile()
        expected_tf_file.add_provider(
            "aws", {"region": "us-east-1", "allowed_account_ids": ["652824372180"]}
        )
        expected_tf_file.add_required_provider(
            "aws", {"source": "hashicorp/aws", "version": "3.73.0"}
        )
        expected_tf_file.add_data("aws_caller_identity", "provider", {})
        expected_tf_file.add_data("aws_region", "provider", {})
        expected_tf_file.add_module(
            "aws-base",
            {
                "env_name": "module-api-test",
                "layer_name": "module-api-test",
                "module_name": "aws-base",
                "private_ipv4_cidr_blocks": [
                    "10.50.128.0/24",
                    "10.50.136.0/24",
                    "10.50.144.0/24",
                ],
                "public_ipv4_cidr_blocks": [
                    "10.50.0.0/24",
                    "10.50.8.0/24",
                    "10.50.16.0/24",
                ],
                "source": mocked_write_args.modules["aws-base"]["source"],
                "total_ipv4_cidr_block": "10.50.0.0/16",
            },
        )

        mocked_write.assert_called_once()
        assert isinstance(mocked_write.call_args.args[0], TerraformFile)
        assert_terraform_file_eq(mocked_write.call_args.args[0], expected_tf_file)


def assert_terraform_file_eq(first: TerraformFile, second: TerraformFile) -> None:
    assert first.__to_json__() == second.__to_json__()
