from click.testing import CliRunner
from pytest import fixture
from pytest_mock import MockFixture

from opta.cli import cli
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module


@fixture(scope="module", autouse=True)
def mock_is_service_config(module_mocker: MockFixture) -> None:
    module_mocker.patch("opta.commands.deploy.is_service_config", return_value=True)


def test_check_layer_and_image_xyz_image_image_flag(mocker: MockFixture) -> None:
    mock_k8s_service_module = mocker.Mock(spec=Module)
    mock_k8s_service_module.name = "test-app"
    mock_k8s_service_module.type = "k8s-service"
    mock_k8s_service_module.data = {"image": "xyz"}

    mock_layer = mocker.Mock(spec=Layer)
    mock_layer.variables = {}
    mock_layer.name = "test"
    mock_layer.org_name = "test_org"
    mock_layer.cloud = "aws"

    mock_layer.modules = [mock_k8s_service_module]
    mock_layer.get_module_by_type.return_value = [mock_k8s_service_module]

    mocker.patch("opta.commands.deploy.opta_acquire_lock")
    mocker.patch("opta.commands.deploy.pre_check")
    mocker.patch("opta.utils.os.path.exists", return_value=True)

    mock_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mock_layer_class.load_from_yaml.return_value = mock_layer

    mock_check_layer_and_image = mocker.patch(
        "opta.commands.deploy.__check_layer_and_image",
        side_effect=UserErrors(
            "Do not pass any image. Image xyz already present in configuration."
        ),
    )
    mocker.patch("opta.commands.deploy.opta_release_lock")
    runner = CliRunner()
    result = runner.invoke(cli, ["deploy", "-i", "app:main"])

    assert result.exit_code == 1
    mock_check_layer_and_image.assert_called_once_with(mock_layer, "app:main")
    assert (
        type(result.exception) == UserErrors
        and result.exception.args
        == UserErrors(
            "Do not pass any image. Image xyz already present in configuration."
        ).args
    )


def test_deploy_basic(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.deploy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy.push_image", return_value=("local_digest", "local_tag")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocker.patch("opta.commands.deploy.__check_layer_and_image", return_value=True)
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
    mocker.patch("opta.commands.deploy.opta_release_lock")
    runner = CliRunner()
    result = runner.invoke(cli, ["deploy", "-i", "local_image:local_tag"])

    assert result.exit_code == 0
    mocked_layer.validate_required_path_dependencies.assert_called_once()
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag",
        config="opta.yaml",
        env=None,
        tag=None,
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocked_layer)
    mock_apply.assert_called_once_with(
        config="opta.yaml",
        env=None,
        refresh=False,
        image_tag=None,
        test=False,
        auto_approve=False,
        image_digest="local_digest",
        detailed_plan=False,
        local=False,
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocker.ANY)


def test_deploy_auto_approve(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.deploy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy.push_image", return_value=("local_digest", "local_tag")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocker.patch("opta.commands.deploy.__check_layer_and_image", return_value=True)
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
    mocker.patch("opta.commands.deploy.opta_release_lock")
    runner = CliRunner()
    result = runner.invoke(
        cli, ["deploy", "-i", "local_image:local_tag", "--auto-approve"]
    )

    assert result.exit_code == 0
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag",
        config="opta.yaml",
        env=None,
        tag=None,
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocked_layer)
    mock_apply.assert_called_once_with(
        config="opta.yaml",
        env=None,
        refresh=False,
        image_tag=None,
        test=False,
        auto_approve=True,
        image_digest="local_digest",
        detailed_plan=False,
        local=False,
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocker.ANY)


def test_deploy_all_flags(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.deploy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy.push_image", return_value=("local_digest", "latest")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocker.patch("opta.commands.deploy.__check_layer_and_image", return_value=True)
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
    mocker.patch("opta.commands.deploy.opta_release_lock")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "deploy",
            "--image",
            "local_image:local_tag",
            "--config",
            "app/opta.yaml",
            "--env",
            "staging",
            "--tag",
            "latest",
        ],
    )

    assert result.exit_code == 0
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag",
        config="app/opta.yaml",
        env="staging",
        tag="latest",
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocked_layer)
    mock_apply.assert_called_once_with(
        config="app/opta.yaml",
        env="staging",
        refresh=False,
        image_tag=None,
        test=False,
        auto_approve=False,
        image_digest="local_digest",
        detailed_plan=False,
        local=False,
        input_variables={},
    )


def test_deploy_ecr_apply(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.deploy.opta_acquire_lock")
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy.push_image", return_value=("local_digest", "latest")
    )
    mocker.patch("opta.commands.deploy.__check_layer_and_image", return_value=True)
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs", return_value={},
    )
    mocker.patch("opta.commands.deploy.opta_release_lock")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "deploy",
            "--image",
            "local_image:local_tag",
            "--config",
            "app/opta.yaml",
            "--env",
            "staging",
            "--tag",
            "latest",
        ],
    )

    assert result.exit_code == 0
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag",
        config="app/opta.yaml",
        env="staging",
        tag="latest",
        input_variables={},
    )
    mock_terraform_outputs.assert_called_once_with(mocked_layer)
    mock_apply.assert_has_calls(
        [
            mocker.call(
                config="app/opta.yaml",
                env="staging",
                refresh=False,
                image_tag=None,
                test=False,
                auto_approve=False,
                stdout_logs=False,
                detailed_plan=False,
                local=False,
                input_variables={},
            ),
            mocker.call(
                config="app/opta.yaml",
                env="staging",
                refresh=False,
                image_tag=None,
                test=False,
                auto_approve=False,
                image_digest="local_digest",
                detailed_plan=False,
                local=False,
                input_variables={},
            ),
        ]
    )
