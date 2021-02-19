import json

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.output import output

TERRAFORM_STATE = {
    "values": {
        "root_module": {
            "resources": [
                {
                    "address": "data.terraform_remote_state.parent",
                    "mode": "data",
                    "type": "terraform_remote_state",
                    "name": "parent",
                    "provider_name": "terraform.io/builtin/terraform",
                    "schema_version": 0,
                    "values": {
                        "backend": "s3",
                        "config": {},
                        "defaults": "None",
                        "outputs": {
                            "k8s_cluster_name": "main",
                            "k8s_endpoint": "https://bla.bla.bla.eks.amazonaws.com",
                            "state_bucket_arn": "arn:aws:s3:::opta-tf-state-runx-staging",
                            "state_bucket_id": "opta-tf-state-runx-staging",
                        },
                        "workspace": "None",
                    },
                }
            ]
        }
    }
}

TERRAFORM_OUTPUTS = {
    "bucket_arn": "arn:aws:s3:::runx-test-bucket-runx-staging",
    "bucket_id": "runx-test-bucket-runx-staging",
    "docker_repo_url": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
}


class TestOutput:
    def test_output(self, mocker: MockFixture) -> None:
        mocker.patch("opta.cli.os.remove")
        mocker.patch("opta.commands.output.gen_all")
        mocker.patch(
            "opta.commands.output.Terraform.get_state", return_value=TERRAFORM_STATE
        )
        mocker.patch(
            "opta.commands.output.Terraform.get_outputs", return_value=TERRAFORM_OUTPUTS
        )

        runner = CliRunner()
        result = runner.invoke(output, ["--include-parent"])
        print(result.exception)
        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "parent.k8s_cluster_name": "main",
            "parent.k8s_endpoint": "https://bla.bla.bla.eks.amazonaws.com",
            "parent.state_bucket_arn": "arn:aws:s3:::opta-tf-state-runx-staging",
            "parent.state_bucket_id": "opta-tf-state-runx-staging",
            "bucket_arn": "arn:aws:s3:::runx-test-bucket-runx-staging",
            "bucket_id": "runx-test-bucket-runx-staging",
            "docker_repo_url": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
        }
