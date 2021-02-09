# type: ignore
import base64
import os

import pytest
from click.testing import CliRunner
from kubernetes.client import CoreV1Api, V1Secret
from pytest_mock import MockFixture, mocker  # noqa

from opta.amplitude import AmplitudeClient, amplitude_client
from opta.module import Module
from opta.plugins.secret_manager import get_module, list_command, update, view


class TestSecretManager:
    def test_get_module_no_configfile(self, mocker: MockFixture):  # noqa
        mocked_path_exists = mocker.patch("os.path.exists")
        mocked_path_exists.return_value = False
        with pytest.raises(Exception):
            get_module("a", "c", "d")
        mocked_path_exists.assert_called_once_with("d")

    def test_get_module_all_good(self):

        target_module = get_module(
            "app",
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
                "dummy-env",
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "plugins",
                    "dummy_config2.yaml",
                ),
            )
            assert "Secret not found" in str(excinfo.value)

    def test_view(self, mocker: MockFixture):  # noqa
        mocked_get_module = mocker.patch("opta.plugins.secret_manager.get_module")
        mocked_module = mocker.Mock(spec=Module)
        mocked_module.layer_name = "dummy_layer"
        mocked_get_module.return_value = mocked_module

        mocked_kube_load_config = mocker.patch(
            "opta.plugins.secret_manager.load_kube_config"
        )

        mocked_kube_client = mocker.patch("opta.plugins.secret_manager.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_response = mocker.Mock(spec=V1Secret)
        mocked_response.data = {
            "dummysecret": base64.b64encode(bytes("supersecret", "utf-8"))
        }
        mocked_client.read_namespaced_secret.return_value = mocked_response

        mocked_amplitude_client = mocker.patch(
            "opta.plugins.secret_manager.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.VIEW_SECRET_EVENT = amplitude_client.VIEW_SECRET_EVENT

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
        mocked_kube_load_config.assert_called_once_with()
        mocked_client.read_namespaced_secret.assert_called_once_with(
            "secret", "dummy_layer"
        )
        mocked_get_module.assert_called_once_with(
            "dummyapp", "dummyenv", "dummyconfigfile"
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.VIEW_SECRET_EVENT
        )

    def test_list_secrets(self, mocker: MockFixture):  # noqa
        mocked_print = mocker.patch("builtins.print")

        mocked_get_module = mocker.patch("opta.plugins.secret_manager.get_module")
        mocked_module = mocker.Mock(spec=Module)
        mocked_module.layer_name = "dummy_layer"
        mocked_get_module.return_value = mocked_module

        mocked_kube_load_config = mocker.patch(
            "opta.plugins.secret_manager.load_kube_config"
        )

        mocked_kube_client = mocker.patch("opta.plugins.secret_manager.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_response = mocker.Mock(spec=V1Secret)
        mocked_response.data = {
            "ALGOLIA_WRITE_KEY": "NmVhNjlmOGM4YjM5NjRjYjZlZmExZTk4MzdjN2Q2OTE="
        }
        mocked_client.read_namespaced_secret.return_value = mocked_response

        mocked_amplitude_client = mocker.patch(
            "opta.plugins.secret_manager.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.LIST_SECRETS_EVENT = amplitude_client.LIST_SECRETS_EVENT

        runner = CliRunner()
        result = runner.invoke(
            list_command,
            ["dummyapp", "--env", "dummyenv", "--configfile", "dummyconfigfile",],
        )
        assert result.exit_code == 0
        mocked_kube_load_config.assert_called_once_with()
        mocked_client.read_namespaced_secret.assert_called_once_with(
            "secret", "dummy_layer"
        )
        mocked_get_module.assert_called_once_with(
            "dummyapp", "dummyenv", "dummyconfigfile"
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.LIST_SECRETS_EVENT
        )
        mocked_print.assert_has_calls([mocker.call("ALGOLIA_WRITE_KEY")])

    def test_update(self, mocker: MockFixture):  # noqa
        mocked_get_module = mocker.patch("opta.plugins.secret_manager.get_module")
        mocked_module = mocker.Mock(spec=Module)
        mocked_module.layer_name = "dummy_layer"
        mocked_get_module.return_value = mocked_module

        mocked_kube_load_config = mocker.patch(
            "opta.plugins.secret_manager.load_kube_config"
        )

        mocked_kube_client = mocker.patch("opta.plugins.secret_manager.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_amplitude_client = mocker.patch(
            "opta.plugins.secret_manager.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.UPDATE_SECRET_EVENT = amplitude_client.UPDATE_SECRET_EVENT

        runner = CliRunner()
        result = runner.invoke(
            update,
            [
                "dummyapp",
                "dummysecret",
                "dummysecretvalue",
                "--env",
                "dummyenv",
                "--configfile",
                "dummyconfigfile",
            ],
        )
        assert result.exit_code == 0
        secret_value = base64.b64encode("dummysecretvalue".encode("utf-8")).decode(
            "utf-8"
        )
        patch = [{"op": "replace", "path": "/data/dummysecret", "value": secret_value}]
        mocked_kube_load_config.assert_called_once_with()
        mocked_client.patch_namespaced_secret.assert_called_once_with(
            "secret", "dummy_layer", patch
        )
        mocked_get_module.assert_called_once_with(
            "dummyapp", "dummyenv", "dummyconfigfile"
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.UPDATE_SECRET_EVENT
        )
