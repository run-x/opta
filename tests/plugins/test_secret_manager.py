# type: ignore
import base64
import os
from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture, mocker  # noqa

from opta.module import Module
from opta.plugins.secret_manager import get_module, view


class TestSecretManager:
    def test_get_module_no_kubectl(self, mocker: MockFixture):  # noqa
        mocked_is_tool = mocker.patch("opta.plugins.secret_manager.is_tool")
        mocked_is_tool.return_value = False
        with pytest.raises(Exception):
            get_module("a", "b", "c", "d")
        mocked_is_tool.assert_called_once_with("kubectl")

    def test_get_module_no_configfile(self, mocker: MockFixture):  # noqa
        mocked_is_tool = mocker.patch("opta.plugins.secret_manager.is_tool")
        mocked_is_tool.return_value = True
        mocked_path_exists = mocker.patch("os.path.exists")
        mocked_path_exists.return_value = False
        with pytest.raises(Exception):
            get_module("a", "b", "c", "d")
        mocked_is_tool.assert_called_once_with("kubectl")
        mocked_path_exists.assert_called_once_with("d")

    def test_get_module_all_good(self):

        target_module = get_module(
            "app",
            "BALONEY",
            "dummy-env",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "plugins",
                "dummy_config1.yaml",
            ),
        )

        assert target_module.key == "app"

    def test_get_module_no_secret(self):
        with pytest.raises(Exception) as excinfo:
            get_module(
                "app",
                "BALONEY",
                "dummy-env",
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "plugins",
                    "dummy_config2.yaml",
                ),
            )
            assert "Secret not found" in str(excinfo.value)

    def test_view(self, mocker: MockFixture):
        mocked_get_module = mocker.patch("opta.plugins.secret_manager.get_module")
        mocked_module = mocker.Mock(spec=Module)
        mocked_module.layer_name = "dummy_layer"
        mocked_get_module.return_value = mocked_module
        mocked_nice_run = mocker.patch("opta.plugins.secret_manager.nice_run")
        mocked_completed_process = mocker.Mock(spec=CompletedProcess)
        mocked_completed_process.returncode = 0
        mocked_completed_process.stdout = base64.b64encode(bytes("supersecret", "utf-8"))
        mocked_nice_run.return_value = mocked_completed_process
        runner = CliRunner()
        result = runner.invoke(
            view,
            [
                "dummyapp",
                "dummysecret",
                "--env",
                "dummyenv",
                "--configfile",
                "dummyconfigfile",
            ],
        )
        assert result.exit_code == 0
        mocked_nice_run.assert_called_once_with(
            [
                "kubectl",
                "get",
                "secrets/secret",
                "--namespace=dummy_layer",
                "--template={{.data.dummysecret}}",
            ],
            capture_output=True,
        )
        mocked_get_module.assert_called_once_with(
            "dummyapp", "dummysecret", "dummyenv", "dummyconfigfile"
        )
