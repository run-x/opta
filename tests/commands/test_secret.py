import os
from typing import Any

from click.testing import CliRunner
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
        mocked_layer.org_name = "dummy_org_name"
        mocked_load_layer.return_value = mocked_layer
        return mocked_load_layer

    def test_view(self, mocker: MockFixture, mocked_layer: Any) -> None:  # noqa
        # Opta file check
        mocked_os_path_exists = mocker.patch("opta.utils.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )

        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch("opta.commands.secret.configure_kubectl")

        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secrets = mocker.patch("opta.commands.secret.get_secrets")
        mocked_get_secrets.return_value = {"dummysecret": "1", "b": "2", "c": "3"}

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.VIEW_SECRET_EVENT = amplitude_client.VIEW_SECRET_EVENT

        runner = CliRunner()
        result = runner.invoke(
            view, ["dummysecret", "--env", "dummyenv", "--config", "dummyconfig"],
        )
        assert result.exit_code == 0
        mocked_create_namespace_if_not_exists.assert_called_once_with("dummy_layer")
        mocked_get_secrets.assert_called_once_with("dummy_layer")
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.VIEW_SECRET_EVENT,
            event_properties={"org_name": "dummy_org_name", "layer_name": "dummy_layer"},
        )

    def test_list_secrets(self, mocker: MockFixture, mocked_layer: Any) -> None:
        mocked_os_path_exists = mocker.patch("opta.utils.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )
        mocked_print = mocker.patch("builtins.print")
        mocker.patch("opta.commands.secret.gen_all")
        mocker.patch("opta.commands.secret.configure_kubectl")

        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secrets = mocker.patch("opta.commands.secret.get_secrets")
        mocked_get_secrets.return_value = {"dummysecret": "1", "b": "2", "c": "3"}

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.LIST_SECRETS_EVENT = amplitude_client.LIST_SECRETS_EVENT

        runner = CliRunner()
        result = runner.invoke(
            list_command, ["--env", "dummyenv", "--config", "dummyconfig"],
        )
        assert result.exit_code == 0
        mocked_create_namespace_if_not_exists.assert_called_once_with("dummy_layer")
        mocked_get_secrets.assert_called_once_with("dummy_layer")
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.LIST_SECRETS_EVENT
        )
        mocked_print.assert_has_calls(
            [mocker.call("dummysecret"), mocker.call("b"), mocker.call("c")]
        )

    def test_update(self, mocker: MockFixture, mocked_layer: Any) -> None:
        # Opta file check
        mocked_os_path_exists = mocker.patch("opta.utils.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )

        mocker.patch("opta.commands.secret.gen_all")
        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_update_manual_secrets = mocker.patch(
            "opta.commands.secret.update_manual_secrets"
        )

        mocker.patch("opta.commands.secret.configure_kubectl")

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
        mocked_create_namespace_if_not_exists.assert_called_once_with("dummy_layer")
        mocked_update_manual_secrets.assert_called_once_with(
            "dummy_layer", {"dummysecret": "dummysecretvalue"}
        )
        mocked_layer.assert_called_once_with("dummyconfig", "dummyenv")
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.UPDATE_SECRET_EVENT
        )
