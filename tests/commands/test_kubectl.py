from subprocess import CompletedProcess

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.kubectl import configure_kubectl
from opta.layer import Layer


def test_configure_kubectl(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    # Mock tf file generation
    mocked_layer_class = mocker.patch("opta.commands.kubectl.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer.name = "blah"
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.root.return_value = mocked_layer
    mocker.patch("opta.commands.kubectl.gen_all")

    # Mock that the kubectl and aws comamnds exist in the env.
    mocked_ensure_installed = mocker.patch("opta.core.kubernetes.ensure_installed")

    # Mock aws commands, including fetching the current aws account id.
    fake_aws_account_id = 1234567890123
    mock_aws_client_instance = mocker.Mock()
    mock_aws_get_caller_identity = {
        "UserId": "mocked_user_id:jd@runx.dev",
        "Account": "1234567890123",
        "Arn": "mocked_arn",
    }
    mock_sts_client = mocker.patch(
        "opta.core.kubernetes.boto3.client", return_value=mock_aws_client_instance
    )
    mock_aws_client_instance.get_caller_identity.return_value = (
        mock_aws_get_caller_identity
    )
    mocked_update_kubeconfig = "Updated context arn... in ../.kube/config"
    mocker.patch(
        "opta.core.kubernetes.nice_run",
        side_effect=[
            CompletedProcess(
                None, 0, mocked_update_kubeconfig.encode("utf-8")  # type: ignore
            ),
        ],
    )

    # Mock fetching the opta env aws account id.
    mocker.patch(
        "opta.core.kubernetes._aws_get_cluster_env",
        return_value=("us-east-1", [f"{fake_aws_account_id}"]),
    )
    # Mock fetching the cluster name
    mocker.patch(
        "opta.core.kubernetes.get_terraform_outputs",
        return_value={"parent.k8s_cluster_name": "main"},
    )

    runner = CliRunner()
    result = runner.invoke(configure_kubectl, [])
    mocked_layer_class.load_from_yaml.assert_called_with("opta.yml", None)
    mock_sts_client.assert_called()
    mocked_ensure_installed.assert_has_calls([mocker.call("kubectl"), mocker.call("aws")])
    assert result.exit_code == 0

    # If the current aws account id does not match the specified opta env's, then
    # raise an exception.
    mock_aws_client_instance = mocker.Mock()
    mock_aws_get_caller_identity = {
        "UserId": "mocked_user_id:jd@runx.dev",
        "Account": "999999999999",
        "Arn": "mocked_arn",
    }
    mock_sts_client = mocker.patch(
        "opta.core.kubernetes.boto3.client", return_value=mock_aws_client_instance
    )
    mock_aws_client_instance.get_caller_identity.return_value = (
        mock_aws_get_caller_identity
    )
    mocker.patch(
        "opta.core.kubernetes.nice_run",
        side_effect=[
            CompletedProcess(
                None, 0, mocked_update_kubeconfig.encode("utf-8")  # type: ignore
            ),
        ],
    )
    result = runner.invoke(configure_kubectl, [])
    mock_sts_client.assert_called()
    assert result.exit_code == 1
    assert "is not configured with the right credentials" in str(result.exception)
