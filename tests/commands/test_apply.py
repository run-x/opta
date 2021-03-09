from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.apply import apply
from opta.constants import TF_PLAN_PATH
from opta.layer import Layer
from opta.module import Module


def test_apply(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.apply.is_tool", return_value=True)
    mocker.patch("opta.commands.apply.amplitude_client.send_event")
    mocker.patch("opta.commands.apply.gen_opta_resource_tags")

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
    mocked_click = mocker.patch("opta.commands.apply.click")
    tf_apply = mocker.patch("opta.commands.apply.Terraform.apply")
    tf_plan = mocker.patch("opta.commands.apply.Terraform.plan")
    tf_show = mocker.patch("opta.commands.apply.Terraform.show")
    tf_create_storage = mocker.patch("opta.commands.apply.Terraform.create_state_storage")

    # Terraform apply should be called with the configured module (fake_module) and the remote state
    # module (deleted_module) as targets.
    runner = CliRunner()
    result = runner.invoke(apply)
    assert result.exit_code == 0
    tf_apply.assert_called_once_with(mocked_layer, TF_PLAN_PATH, no_init=True, quiet=True)
    tf_plan.assert_called_once_with(
        "-lock=false",
        "-input=false",
        f"-out={TF_PLAN_PATH}",
        "-target=module.deletedmodule",
        "-target=module.fakemodule",
        quiet=True,
    )
    mocked_click.confirm.assert_called_once_with(
        "The above are the planned changes for your opta run. Do you approve?",
        abort=True,
    )
    tf_show.assert_called_once_with(TF_PLAN_PATH)
    tf_create_storage.assert_called_once_with(mocked_layer)
