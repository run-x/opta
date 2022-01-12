from subprocess import CompletedProcess

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.kubectl import configure_kubectl
from opta.layer import Layer


def test_configure_kubectl(mocker: MockFixture) -> None:
    # Mock tf file generation
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
    mocked_load_opta_config_to_default = mocker.patch(
        "opta.commands.kubectl.load_opta_config_to_default"
    )

    runner = CliRunner()
    result = runner.invoke(configure_kubectl, [])
    assert result.exit_code == 0
    mocked_layer_class.load_from_yaml.assert_called_with(mocker.ANY, None)
    mocked_layer.verify_cloud_credentials.assert_called_once_with()
    mocked_configure.assert_called_once_with(mocked_layer)
    mocked_load_opta_config_to_default.assert_called_once_with(mocked_layer)
    mocked_check_opta_file_exists.assert_called_once_with("opta.yaml")

    # # Mock that the kubectl and aws comamnds exist in the env.
    # mocked_ensure_installed = mocker.patch("opta.core.kubernetes.ensure_installed")
    #
    # # Mock aws commands, including fetching the current aws account id.
    # fake_aws_account_id = 1234567890123
    # mock_eks_client = mocker.Mock()
    # mocker.patch("opta.core.kubernetes.boto3.client", return_value=mock_eks_client)
    # mock_eks_client.describe_cluster.return_value = {
    #     "cluster": {
    #         "certificateAuthority": {"data": "ca-data"},
    #         "endpoint": "eks-endpoint",
    #     }
    # }
    # mocked_update_kubeconfig = "Updated context arn... in ../.kube/config"
    # mocker.patch(
    #     "opta.core.kubernetes.nice_run",
    #     side_effect=[
    #         CompletedProcess(
    #             None, 0, mocked_update_kubeconfig.encode("utf-8")  # type: ignore
    #         ),
    #     ],
    # )
    #
    # # Mock fetching the opta env aws account id.
    # mocker.patch(
    #     "opta.core.kubernetes._aws_get_cluster_env",
    #     return_value=("us-east-1", [f"{fake_aws_account_id}"]),
    # )
    # # Mock fetching the cluster name
    # mocker.patch(
    #     "opta.core.kubernetes.get_terraform_outputs",
    #     return_value={"parent.k8s_cluster_name": "main"},
    # )
    #
    # runner = CliRunner()
    # result = runner.invoke(configure_kubectl, [])
    # mocked_layer_class.load_from_yaml.assert_called_with("opta.yaml", None)
    # mocked_ensure_installed.assert_has_calls([mocker.call("kubectl")])
    # assert result.exit_code == 0
