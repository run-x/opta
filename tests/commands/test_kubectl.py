import json
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
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.root.return_value = mocked_layer
    mocker.patch("opta.commands.kubectl.gen_all")

    # Mock that the kubectl and aws comamnds exist in the env.
    mocker.patch("opta.core.kubernetes.is_tool", return_value=True)

    # Mock aws commands, including fetching the current aws account id.
    fake_aws_account_id = 1234567890123
    mocked_caller_identity = json.dumps(
        {
            "UserId": "bla",
            "Account": f"{fake_aws_account_id}",
            "Arn": "arn:aws:iam::979926061731:user/test",
        }
    )
    mocked_update_kubeconfig = "Updated context arn... in ../.kube/config"
    mocker.patch(
        "opta.core.kubernetes.nice_run",
        side_effect=[
            CompletedProcess(None, 0, mocked_caller_identity.encode("utf-8")),  # type: ignore
            CompletedProcess(None, 0, mocked_update_kubeconfig.encode("utf-8")),  # type: ignore
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
    assert result.exit_code == 0

    # If the current aws account id does not match the specified opta env's, then
    # raise an exception.
    mocked_caller_identity = json.dumps(
        {
            "UserId": "bla",
            "Account": "999999999999",
            "Arn": "arn:aws:iam::979926061731:user/test",
        }
    )
    mocker.patch(
        "opta.core.kubernetes.nice_run",
        side_effect=[
            CompletedProcess(None, 0, mocked_caller_identity.encode("utf-8")),  # type: ignore
            CompletedProcess(None, 0, mocked_update_kubeconfig.encode("utf-8")),  # type: ignore
        ],
    )
    result = runner.invoke(configure_kubectl, [])
    assert result.exit_code == 1
    assert "is not configured with the right credentials" in str(result.exception)
