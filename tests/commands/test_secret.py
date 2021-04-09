import base64
from typing import Any

from click.testing import CliRunner
from kubernetes.client import CoreV1Api, V1Secret
from pytest import fixture
from pytest_mock import MockFixture

from opta.amplitude import AmplitudeClient, amplitude_client
from opta.commands.secret import list_command, update, view
from opta.layer import Layer


class TestSecretManager:
    @fixture
    def mocked_layer(self, mocker: MockFixture) -> Any:
        mocked_load_layer = mocker.patch("opta.commands.secret.Layer.load_from_yaml")
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.name = "dummy_layer"
        mocked_layer.cloud = "aws"
        mocked_load_layer.return_value = mocked_layer
        return mocked_load_layer

    def test_eks_cluster_doesnt_exist(
        self, mocker: MockFixture, mocked_layer: Any
    ) -> None:
        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch(
            "opta.commands.secret.fetch_terraform_state_resources", return_value={}
        )
        runner = CliRunner()
        result = runner.invoke(update, ["dummysecret", "dummysecretvalue"])
        assert "there was no K8s cluster found in the opta state" in str(result.exception)

    def test_view(self, mocker: MockFixture, mocked_layer: Any) -> None:  # noqa
        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch("opta.commands.secret._raise_if_no_k8s_cluster_exists")
        mocker.patch("opta.commands.secret.configure_kubectl")

        mocked_kube_load_config = mocker.patch("opta.commands.secret.load_kube_config")

        mocked_kube_client = mocker.patch("opta.commands.secret.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_response = mocker.Mock(spec=V1Secret)
        mocked_response.data = {
            "dummysecret": base64.b64encode(bytes("supersecret", "utf-8"))
        }
        mocked_client.read_namespaced_secret.return_value = mocked_response

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.VIEW_SECRET_EVENT = amplitude_client.VIEW_SECRET_EVENT

        runner = CliRunner()
        result = runner.invoke(
            view, ["dummysecret", "--env", "dummyenv", "--config", "dummyconfig"],
        )
        assert result.exit_code == 0
        mocked_kube_load_config.assert_called_once_with()
        mocked_client.read_namespaced_secret.assert_called_once_with(
            "secret", "dummy_layer"
        )
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.VIEW_SECRET_EVENT
        )

    def test_list_secrets(self, mocker: MockFixture, mocked_layer: Any) -> None:
        mocked_print = mocker.patch("builtins.print")
        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch("opta.commands.secret._raise_if_no_k8s_cluster_exists")
        mocker.patch("opta.commands.secret.configure_kubectl")

        mocked_kube_load_config = mocker.patch("opta.commands.secret.load_kube_config")

        mocked_kube_client = mocker.patch("opta.commands.secret.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_response = mocker.Mock(spec=V1Secret)
        mocked_response.data = {
            "ALGOLIA_WRITE_KEY": "NmVhNjlmOGM4YjM5NjRjYjZlZmExZTk4MzdjN2Q2OTE="
        }
        mocked_client.read_namespaced_secret.return_value = mocked_response

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.LIST_SECRETS_EVENT = amplitude_client.LIST_SECRETS_EVENT

        runner = CliRunner()
        result = runner.invoke(
            list_command, ["--env", "dummyenv", "--config", "dummyconfig"],
        )
        assert result.exit_code == 0
        mocked_kube_load_config.assert_called_once_with()
        mocked_client.read_namespaced_secret.assert_called_once_with(
            "secret", "dummy_layer"
        )
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.LIST_SECRETS_EVENT
        )
        mocked_print.assert_has_calls([mocker.call("ALGOLIA_WRITE_KEY")])

    def test_update(self, mocker: MockFixture, mocked_layer: Any) -> None:
        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch("opta.commands.secret.configure_kubectl")
        mocker.patch("opta.commands.secret._raise_if_no_k8s_cluster_exists")

        mocked_kube_load_config = mocker.patch("opta.commands.secret.load_kube_config")

        mocked_kube_client = mocker.patch("opta.commands.secret.CoreV1Api")
        mocked_client = mocker.Mock(spec=CoreV1Api)
        mocked_kube_client.return_value = mocked_client

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.UPDATE_SECRET_EVENT = amplitude_client.UPDATE_SECRET_EVENT

        runner = CliRunner()
        result = runner.invoke(
            update,
            [
                "dummysecret",
                "dummysecretvalue",
                "--env",
                "dummyenv",
                "--config",
                "dummyconfig",
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
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.UPDATE_SECRET_EVENT
        )
