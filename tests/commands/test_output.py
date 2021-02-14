import json
from typing import List

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.output import output

TERRAFORM_SHOW_JSON = {
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

TERRAFORM_OUTPUT_JSON = {
    "bucket_arn": {
        "sensitive": False,
        "type": "string",
        "value": "arn:aws:s3:::runx-test-bucket-runx-staging",
    },
    "bucket_id": {
        "sensitive": False,
        "type": "string",
        "value": "runx-test-bucket-runx-staging",
    },
    "docker_repo_url": {
        "sensitive": False,
        "type": "string",
        "value": "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app",
    },
}


class MockedCmdOut:
    def __init__(self, out: dict):
        self.stdout = json.dumps(out).encode("utf-8")


class TestOutput:
    def mock_shell_cmds(self, *args: List, **kwargs: dict) -> MockedCmdOut:
        ret: dict = {}
        if args[0] == ["terraform", "show", "-json"]:
            ret = TERRAFORM_SHOW_JSON
        elif args[0] == ["terraform", "output", "-json"]:
            ret = TERRAFORM_OUTPUT_JSON

        return MockedCmdOut(ret)

    def test_output(self, mocker: MockFixture) -> None:
        mocker.patch("opta.cli.os.remove")
        mocker.patch("opta.commands.output.gen")
        mocker.patch("opta.commands.output.nice_run", side_effect=self.mock_shell_cmds)

        runner = CliRunner()
        result = runner.invoke(output, ["--include-parent"])
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
