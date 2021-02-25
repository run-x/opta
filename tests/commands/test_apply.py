from unittest.mock import ANY

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.apply import apply
from opta.layer import Layer
from opta.module import Module


def test_apply(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.apply.is_tool", return_value=True)
    mocker.patch("opta.commands.apply.amplitude_client.send_event")

    mocked_layer_class = mocker.patch("opta.commands.apply.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.variables = {}
    mocked_layer_class.load_from_yaml.return_value = mocked_layer

    # Mock remote state
    mocker.patch(
        "opta.commands.apply.Terraform.get_existing_modules",
        return_value={"deletedmodule"},
    )

    # Mock opta config
    fake_module = Module("test", data={"type": "k8s-service", "name": "fakemodule"})
    mocker.patch("opta.commands.apply.gen", return_value=iter([(0, [fake_module], 1)]))
    tf_apply = mocker.patch("opta.commands.apply.Terraform.apply")
    tf_create_storage = mocker.patch("opta.commands.apply.Terraform.create_state_storage")

    # Terraform apply should be called with the configured module (fake_module) and the remote state
    # module (deleted_module) as targets.
    runner = CliRunner()
    result = runner.invoke(apply)
    assert result.exit_code == 0
    tf_apply.assert_called_once_with(
        ANY, "-target=module.deletedmodule", "-target=module.fakemodule"
    )
    tf_create_storage.assert_called_once_with(mocked_layer)
