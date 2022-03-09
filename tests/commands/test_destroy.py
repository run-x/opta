import os

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.destroy import destroy
from opta.constants import TF_PLAN_PATH
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module
from tests.util import get_call_args

FAKE_ENV_CONFIG = os.path.join(
    os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
)

FAKE_SERVICE_CONFIG = os.path.join(
    os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
)

FAKE_SERVICE_CONFIG_MULTIPLE_ENV = os.path.join(
    os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_2_env.yml",
)


def test_destroy_env_with_children(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.opta_acquire_lock")
    mocker.patch(
        "opta.commands.destroy.Terraform.tf_lock_details", return_value=(False, ""),
    )
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=["a", "b"],
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")
    mocker.patch("opta.commands.destroy.opta_release_lock")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    assert result.exit_code == 1
    assert isinstance(result.exception, UserErrors)

    assert not mocked_gen_all.called


def test_destroy_env_without_children(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_modules = [mocker.Mock(spec=Module) for _ in range(3)]
    for i, module in enumerate(mock_modules):
        module.name = f"fake_module_{i}"

    mock_layer = mocker.Mock(spec=Layer)
    mock_layer.name = "dummy-parent"
    mock_layer.cloud = "aws"
    mock_layer.modules = mock_modules

    mocker.patch("opta.commands.destroy.Layer.load_from_yaml", return_value=mock_layer)
    mocker.patch(
        "opta.commands.destroy.Terraform.tf_lock_details", return_value=(False, "")
    )
    mocker.patch("opta.commands.destroy._fetch_children_layers", return_value=None)
    mocker.patch("opta.commands.destroy.click.confirm", return_value=True)
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch(
        "opta.commands.destroy.Terraform.get_existing_modules", return_value={"base"}
    )
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    mock_terraform_init = mocker.patch(
        "opta.commands.destroy.Terraform.init", return_value=None
    )
    mock_terraform_refresh = mocker.patch(
        "opta.commands.destroy.Terraform.refresh", return_value=None
    )
    mock_terraform_plan = mocker.patch(
        "opta.commands.destroy.Terraform.plan", return_value=None
    )
    mock_terraform_plan_displayer = mocker.patch(
        "opta.commands.destroy.PlanDisplayer.display", return_value=None
    )
    mock_terraform_apply = mocker.patch(
        "opta.commands.destroy.Terraform.apply", return_value=None
    )
    mock_terraform_delete_storage_state = mocker.patch(
        "opta.commands.destroy.Terraform.delete_state_storage", return_value=None
    )

    mocker.patch(
        "opta.core.terraform.Terraform.get_existing_modules",
        return_value={"fake_module_2", "fake_module_1", "fake_module_0"},
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")
    mocker.patch("opta.commands.destroy.opta_release_lock")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    assert result.exit_code == 0

    mock_terraform_init.assert_called_once_with(False, "-reconfigure", layer=mock_layer)
    mock_terraform_refresh.assert_called_once_with(mock_layer)
    mock_terraform_plan.assert_has_calls(
        [
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_2"]),
            ),
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_1"]),
            ),
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_0"]),
            ),
        ]
    )
    mock_terraform_plan_displayer.assert_has_calls(
        [
            mocker.call(detailed_plan=False),
            mocker.call(detailed_plan=False),
            mocker.call(detailed_plan=False),
        ]
    )

    mock_terraform_apply.assert_has_calls(
        [
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
        ]
    )

    mock_terraform_delete_storage_state.assert_called_once_with(mock_layer)

    args = get_call_args(mocked_gen_all)

    assert len(args) == 1
    assert args[0].name == "dummy-parent"


def test_destroy_service(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_modules = [mocker.Mock(spec=Module) for _ in range(3)]
    for i, module in enumerate(mock_modules):
        module.name = f"fake_module_{i}"

    mock_layer = mocker.Mock(spec=Layer)
    mock_layer.name = "dummy-config"
    mock_layer.cloud = "aws"
    mock_layer.modules = mock_modules

    mocker.patch("opta.commands.destroy.Layer.load_from_yaml", return_value=mock_layer)
    mocker.patch(
        "opta.commands.destroy.Terraform.tf_lock_details", return_value=(False, "")
    )
    mocker.patch("opta.commands.destroy._fetch_children_layers", return_value=None)
    mocker.patch("opta.commands.destroy.click.confirm", return_value=True)
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch(
        "opta.commands.destroy.Terraform.get_existing_modules", return_value={"base"}
    )
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    mock_terraform_init = mocker.patch(
        "opta.commands.destroy.Terraform.init", return_value=None
    )
    mock_terraform_refresh = mocker.patch(
        "opta.commands.destroy.Terraform.refresh", return_value=None
    )
    mock_terraform_plan = mocker.patch(
        "opta.commands.destroy.Terraform.plan", return_value=None
    )
    mock_terraform_plan_displayer = mocker.patch(
        "opta.commands.destroy.PlanDisplayer.display", return_value=None
    )
    mock_terraform_apply = mocker.patch(
        "opta.commands.destroy.Terraform.apply", return_value=None
    )
    mock_terraform_delete_storage_state = mocker.patch(
        "opta.commands.destroy.Terraform.delete_state_storage", return_value=None
    )

    mocker.patch(
        "opta.core.terraform.Terraform.get_existing_modules",
        return_value={"fake_module_2", "fake_module_1", "fake_module_0"},
    )

    mocked_gen_all = mocker.patch("opta.commands.destroy.gen_all")
    mocker.patch("opta.commands.destroy.opta_release_lock")

    runner = CliRunner()
    result = runner.invoke(destroy, ["--config", FAKE_ENV_CONFIG])

    assert result.exit_code == 0

    mock_terraform_init.assert_called_once_with(False, "-reconfigure", layer=mock_layer)
    mock_terraform_refresh.assert_called_once_with(mock_layer)
    mock_terraform_plan.assert_has_calls(
        [
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_2"]),
            ),
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_1"]),
            ),
            mocker.call(
                "-lock=false",
                "-input=false",
                "-destroy",
                f"-out={TF_PLAN_PATH}",
                layer=mock_layer,
                *list(["-target=module.fake_module_0"]),
            ),
        ]
    )
    mock_terraform_plan_displayer.assert_has_calls(
        [
            mocker.call(detailed_plan=False),
            mocker.call(detailed_plan=False),
            mocker.call(detailed_plan=False),
        ]
    )

    mock_terraform_apply.assert_has_calls(
        [
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
            mocker.call(mock_layer, TF_PLAN_PATH, no_init=True, quiet=False),
        ]
    )

    mock_terraform_delete_storage_state.assert_called_once_with(mock_layer)

    args = get_call_args(mocked_gen_all)

    assert len(args) == 1
    assert args[0].name == "dummy-config"


def test_destroy_service_single_env_wrong_input(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    runner = CliRunner()
    """Actual ENV present in the Service YML is dummy-env"""
    result = runner.invoke(destroy, ["--config", FAKE_SERVICE_CONFIG, "--env", "dummy"])

    assert result.exit_code == 1


def test_destroy_service_multiple_env_wrong_input(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.destroy.amplitude_client.send_event")
    mocker.patch("opta.commands.destroy.Terraform.init")
    mocker.patch("opta.commands.destroy.Terraform.download_state", return_value=True)
    mocker.patch("opta.commands.destroy.Layer.verify_cloud_credentials")

    mocker.patch(
        "opta.commands.destroy._aws_get_configs", return_value=[],
    )

    runner = CliRunner()
    """Actual ENV present in the Service YML are (dummy-env, dummy-env-2)"""
    result = runner.invoke(
        destroy, ["--config", FAKE_SERVICE_CONFIG_MULTIPLE_ENV, "--env", "dummy"]
    )

    assert result.exit_code == 1
