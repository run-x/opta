import os
from typing import Any

from click.testing import CliRunner
from pytest import fixture
from pytest_mock import MockFixture

from opta.amplitude import AmplitudeClient, amplitude_client
from opta.commands.secret import bulk_update, delete, list_command, update, view
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
        mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )

        mocker.patch("opta.commands.secret.set_kube_config")

        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secret_name_and_namespace = mocker.patch(
            "opta.commands.secret.get_secret_name_and_namespace"
        )
        mocked_get_secret_name_and_namespace.return_value = [
            "manual-secrets",
            "dummy_layer",
        ]
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
        mocked_get_secrets.assert_called_once_with("dummy_layer", "manual-secrets")
        mocked_layer.assert_called_once_with(
            "dummyconfig", "dummyenv", input_variables={}, strict_input_variables=False
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.VIEW_SECRET_EVENT,
            event_properties={"org_name": "dummy_org_name", "layer_name": "dummy_layer"},
        )

    def test_list_secrets(self, mocker: MockFixture, mocked_layer: Any) -> None:
        mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )
        mocked_print = mocker.patch("builtins.print")
        mocker.patch("opta.commands.secret.set_kube_config")

        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secret_name_and_namespace = mocker.patch(
            "opta.commands.secret.get_secret_name_and_namespace"
        )
        mocked_get_secret_name_and_namespace.return_value = [
            "manual-secrets",
            "dummy_layer",
        ]
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
        mocked_get_secrets.assert_called_once_with("dummy_layer", "manual-secrets")
        mocked_layer.assert_called_once_with(
            "dummyconfig", "dummyenv", input_variables={}, strict_input_variables=False
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.LIST_SECRETS_EVENT
        )
        mocked_print.assert_has_calls(
            [mocker.call("dummysecret=1"), mocker.call("b=2"), mocker.call("c=3")]
        )

    def test_delete_secret(self, mocker: MockFixture, mocked_layer: Any) -> None:
        # Opta file check
        mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )

        mocked_check_if_namespace_exists = mocker.patch(
            "opta.commands.secret.check_if_namespace_exists"
        )
        mocked_get_secret_name_and_namespace = mocker.patch(
            "opta.commands.secret.get_secret_name_and_namespace"
        )
        mocked_get_secret_name_and_namespace.return_value = [
            "manual-secrets",
            "dummy_layer",
        ]
        mocked_delete_secret_key = mocker.patch("opta.commands.secret.delete_secret_key")
        mocked_restart_deployments = mocker.patch(
            "opta.commands.secret.restart_deployments"
        )
        mocker.patch("opta.command" "s.secret.set_kube_config")

        mocked_amplitude_client = mocker.patch(
            "opta.commands.secret.amplitude_client", spec=AmplitudeClient
        )
        mocked_amplitude_client.UPDATE_SECRET_EVENT = amplitude_client.UPDATE_SECRET_EVENT

        runner = CliRunner()
        result = runner.invoke(
            delete, ["dummysecret", "--env", "dummyenv", "--config", "dummyconfig"]
        )
        assert result.exit_code == 0
        mocked_check_if_namespace_exists.assert_called_once_with("dummy_layer")
        mocked_delete_secret_key.assert_called_once_with(
            "dummy_layer", "manual-secrets", "dummysecret"
        )
        mocked_layer.assert_called_once_with(
            "dummyconfig", "dummyenv", input_variables={}, strict_input_variables=False
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.UPDATE_SECRET_EVENT
        )
        mocked_restart_deployments.assert_called_once_with("dummy_layer")

        # test updating a secret that is not listed in the config file - should work
        result = runner.invoke(delete, ["unlistedsecret"])
        assert result.exit_code == 0
        mocked_delete_secret_key.assert_called_with(
            "dummy_layer", "manual-secrets", "unlistedsecret"
        )

    def test_update(self, mocker: MockFixture, mocked_layer: Any) -> None:
        # Opta file check
        mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
        mocked_os_path_exists.return_value = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
        )

        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secret_name_and_namespace = mocker.patch(
            "opta.commands.secret.get_secret_name_and_namespace"
        )
        mocked_get_secret_name_and_namespace.return_value = [
            "manual-secrets",
            "dummy_layer",
        ]
        mocked_update_secrets = mocker.patch("opta.commands.secret.update_secrets")
        mocked_restart_deployments = mocker.patch(
            "opta.commands.secret.restart_deployments"
        )
        mocker.patch("opta.commands.secret.set_kube_config")

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
        mocked_update_secrets.assert_called_once_with(
            "dummy_layer", "manual-secrets", {"dummysecret": "dummysecretvalue"}
        )
        mocked_layer.assert_called_once_with(
            "dummyconfig", "dummyenv", input_variables={}, strict_input_variables=False
        )
        mocked_amplitude_client.send_event.assert_called_once_with(
            amplitude_client.UPDATE_SECRET_EVENT
        )
        mocked_restart_deployments.assert_called_once_with("dummy_layer")

        # test updating a secret that is not listed in the config file - should work
        result = runner.invoke(update, ["unlistedsecret", "newvalue"])
        assert result.exit_code == 0
        mocked_update_secrets.assert_called_with(
            "dummy_layer", "manual-secrets", {"unlistedsecret": "newvalue"}
        )

    def test_bulk_update(self, mocker: MockFixture, mocked_layer: Any) -> None:
        env_file = os.path.join(
            os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_secrets.env"
        )
        mocker.patch("opta.utils.os.path.exists")
        mocker.patch("opta.commands.secret.set_kube_config")
        mocked_create_namespace_if_not_exists = mocker.patch(
            "opta.commands.secret.create_namespace_if_not_exists"
        )
        mocked_get_secret_name_and_namespace = mocker.patch(
            "opta.commands.secret.get_secret_name_and_namespace"
        )
        mocked_get_secret_name_and_namespace.return_value = [
            "manual-secrets",
            "dummy_layer",
        ]
        mocked_update_secrets = mocker.patch("opta.core.secrets.update_secrets")
        mocked_amplitude_event = mocker.patch(
            "opta.commands.secret.amplitude_client.send_event"
        )
        mocked_restart_deployments = mocker.patch(
            "opta.commands.secret.restart_deployments"
        )

        runner = CliRunner()
        result = runner.invoke(
            bulk_update, [env_file, "--env", "dummyenv", "--config", "dummyconfig"],
        )
        assert result.exit_code == 0
        mocked_create_namespace_if_not_exists.assert_called_once_with("dummy_layer")
        # check each secret from the env file was updated
        mocked_update_secrets.assert_called_once_with(
            "dummy_layer",
            "manual-secrets",
            {"FROM_FILE_SECRET1": "val1", "FROM_FILE_SECRET2": "1"},
        )

        mocked_layer.assert_called_once_with(
            "dummyconfig", "dummyenv", input_variables={}, strict_input_variables=False
        )
        mocked_amplitude_event.assert_called_once_with(
            amplitude_client.UPDATE_BULK_SECRET_EVENT
        )
        mocked_restart_deployments.assert_called_once_with("dummy_layer")

        # test deployment is not restarted with flag --no-restart
        mocked_restart_deployments.reset_mock()
        result = runner.invoke(
            bulk_update,
            [env_file, "--env", "dummyenv", "--config", "--no-restart", "dummyconfig"],
        )
        mocked_restart_deployments.assert_not_called()
