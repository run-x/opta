import json
from subprocess import CompletedProcess

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.kubectl import configure_kubectl


class TestKubectl:
    def test_configure_kubectl(self, mocker: MockFixture) -> None:
        # Mock tf file generation
        mocker.patch("opta.commands.kubectl.gen_all")

        # Mock that the kubectl and aws comamnds exist in the env.
        mocker.patch("opta.commands.kubectl.is_tool", return_value=True)

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
            "opta.commands.kubectl.nice_run",
            side_effect=[
                CompletedProcess(None, 0, mocked_caller_identity.encode("utf-8")),  # type: ignore
                CompletedProcess(None, 0, mocked_update_kubeconfig.encode("utf-8")),  # type: ignore
            ],
        )

        # Mock fetching the opta env aws account id.
        mocker.patch("opta.commands.kubectl._get_root_layer")
        mocker.patch(
            "opta.commands.kubectl._get_cluster_env",
            return_value=("us-east-1", [fake_aws_account_id]),
        )
        # Mock fetching the cluster name
        mocker.patch(
            "opta.commands.kubectl.get_terraform_outputs",
            return_value={"parent.k8s_cluster_name": "main"},
        )

        runner = CliRunner()
        result = runner.invoke(configure_kubectl, [])
        print(result.exception)
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
            "opta.commands.kubectl.nice_run",
            side_effect=[
                CompletedProcess(None, 0, mocked_caller_identity.encode("utf-8")),  # type: ignore
                CompletedProcess(None, 0, mocked_update_kubeconfig.encode("utf-8")),  # type: ignore
            ],
        )
        result = runner.invoke(configure_kubectl, [])
        assert result.exit_code == 1
        assert "is not configured with the right credentials" in str(result.exception)
