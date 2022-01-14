from click.testing import CliRunner
from pytest import fixture
from pytest_mock import MockFixture

from opta.cli import cli
from opta.layer import Layer


@fixture(scope="module", autouse=True)
def mock_is_service_config(module_mocker: MockFixture) -> None:
    module_mocker.patch("opta.commands.deploy.is_service_config", return_value=True)


def test_deploy_basic(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy._push", return_value=("local_digest", "local_tag")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["deploy", "-i", "local_image:local_tag"])

    assert result.exit_code == 0
    mocked_layer.validate_required_path_dependencies.assert_called_once()
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag", config="opta.yaml", env=None, tag=None
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
    )
    mock_terraform_outputs.assert_called_once_with(mocker.ANY)


def test_deploy_auto_approve(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy._push", return_value=("local_digest", "local_tag")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
    runner = CliRunner()
    result = runner.invoke(
        cli, ["deploy", "-i", "local_image:local_tag", "--auto-approve"]
    )

    assert result.exit_code == 0
    mock_tf_download_state.assert_called_once_with(mocked_layer)
    mock_push.assert_called_once_with(
        image="local_image:local_tag", config="opta.yaml", env=None, tag=None
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
    )
    mock_terraform_outputs.assert_called_once_with(mocker.ANY)


def test_deploy_all_flags(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy._push", return_value=("local_digest", "latest")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs",
        return_value={"docker_repo_url": "blah"},
    )
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
        image="local_image:local_tag", config="app/opta.yaml", env="staging", tag="latest"
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
    )


def test_deploy_ecr_apply(mocker: MockFixture) -> None:
    mocked_os_path_exists = mocker.patch("opta.utils.exists")
    mocked_os_path_exists.return_value = True
    mock_tf_download_state = mocker.patch(
        "opta.commands.deploy.Terraform.download_state", return_value=True
    )
    mocker.patch(
        "opta.commands.deploy.Terraform.tf_lock_details", return_value=(False, ""),
    )

    mock_push = mocker.patch(
        "opta.commands.deploy._push", return_value=("local_digest", "latest")
    )
    mock_apply = mocker.patch("opta.commands.deploy._apply")
    mocked_layer_class = mocker.patch("opta.commands.deploy.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mock_terraform_outputs = mocker.patch(
        "opta.commands.deploy.Terraform.get_outputs", return_value={},
    )
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
        image="local_image:local_tag", config="app/opta.yaml", env="staging", tag="latest"
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
            ),
        ]
    )
