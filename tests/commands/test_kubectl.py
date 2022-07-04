from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.kubectl import configure_kubectl
from opta.layer import Layer


def test_set_kube_config(mocker: MockFixture) -> None:
    # Mock tf file generation
    mocker.patch("opta.commands.kubectl.opta_acquire_lock")
    mocked_layer_class = mocker.patch("opta.commands.kubectl.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer.name = "blah"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.root.return_value = mocked_layer

    mocked_configure = mocker.patch("opta.commands.kubectl.configure")
    mocked_check_opta_file_exists = mocker.patch(
        "opta.commands.kubectl.check_opta_file_exists"
    )
    mocked_purge_opta_kube_config = mocker.patch(
        "opta.commands.kubectl.purge_opta_kube_config"
    )
    mocked_load_opta_kube_config_to_default = mocker.patch(
        "opta.commands.kubectl.load_opta_kube_config_to_default"
    )
    mocker.patch("opta.commands.kubectl.opta_release_lock")

    runner = CliRunner()
    result = runner.invoke(configure_kubectl, [])
    assert result.exit_code == 0
    mocked_layer_class.load_from_yaml.assert_called_with(
        mocker.ANY, None, input_variables={}, strict_input_variables=False
    )
    mocked_layer.verify_cloud_credentials.assert_called_once_with()
    mocked_configure.assert_called_once_with(mocked_layer)
    mocked_purge_opta_kube_config.assert_called_once_with(mocked_layer)
    mocked_load_opta_kube_config_to_default.assert_called_once_with(mocked_layer)
    mocked_check_opta_file_exists.assert_called_once_with("opta.yaml")
