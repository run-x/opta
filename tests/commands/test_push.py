import base64
import json
from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli
from opta.commands.push import get_ecr_auth_info, get_registry_url, push_to_docker
from opta.layer import Layer
from tests.commands.test_output import TERRAFORM_OUTPUT_JSON
from tests.fixtures.apply import BASIC_APPLY

REGISTRY_URL = TERRAFORM_OUTPUT_JSON["docker_repo_url"]["value"]


class TestGetRegistryUrl:
    def get_mocked_shell_cmds(self, mocker: MockFixture, tf_output_dict: dict) -> Any:
        def mocked_shell_cmds(args_array: List[str], **kwargs: Any) -> Any:
            mocked_terraform_init = mocker.Mock(spec=CompletedProcess)
            mocked_terraform_output = mocker.Mock(spec=CompletedProcess)
            mocked_terraform_output.stdout = json.dumps(tf_output_dict).encode("utf-8")

            if args_array == ["terraform", "init"]:
                return mocked_terraform_init
            if args_array == ["terraform", "output", "-json"]:
                return mocked_terraform_output
            raise Exception("Unexpected test input")

        return mocked_shell_cmds

    def test_works(self, mocker: MockFixture) -> None:  # noqa
        mocked_parent = mocker.patch("opta.commands.output._fetch_parent_outputs")
        mocked_parent.return_value = {}

        nice_run_mock = mocker.patch(
            "opta.commands.output.nice_run",
            side_effect=self.get_mocked_shell_cmds(mocker, TERRAFORM_OUTPUT_JSON,),
        )

        docker_repo_url = get_registry_url()
        nice_run_mock.assert_has_calls(
            [
                mocker.call(
                    ["terraform", "output", "-json"], check=True, capture_output=True
                ),
            ]
        )
        assert docker_repo_url == REGISTRY_URL

    def test_no_docker_repo_url_in_output(self, mocker: MockFixture) -> None:
        mocked_isdir = mocker.patch("os.path.isdir")
        mocked_isdir.return_value = True

        mocker.patch(
            "opta.commands.push.nice_run",
            side_effect=self.get_mocked_shell_cmds(mocker, {},),
        )

        with pytest.raises(Exception) as e_info:
            get_registry_url()

        expected_error_output = "Unable to determine docker repository url. There is likely something wrong with your opta configuration."
        assert expected_error_output in str(e_info)


class TestGetEcrAuthInfo:
    def test_get_ecr_auth_info(self, mocker: MockFixture) -> None:
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.gen_providers = lambda x, y: BASIC_APPLY[1]

        mocked_ecr_client = mocker.Mock()

        def mock_get_authorization_token(registryIds: List[str]) -> Dict[str, Any]:
            decoded_auth_token = "username:password"
            auth_token_bytes = decoded_auth_token.encode()
            b64_auth_token = base64.b64encode(auth_token_bytes)
            return {"authorizationData": [{"authorizationToken": b64_auth_token}]}

        mocked_ecr_client.get_authorization_token = mock_get_authorization_token
        patched_boto_client = mocker.patch("opta.commands.push.boto3.client")
        patched_boto_client.return_value = mocked_ecr_client

        def mocked_load_from_yaml(config: str, env: Optional[str]) -> Layer:
            return mocked_layer

        mocker.patch.object(Layer, "load_from_yaml", new=mocked_load_from_yaml)
        assert get_ecr_auth_info(config="opta.yml", env="runx-staging") == (
            "username",
            "password",
        )


class TestPushToDocker:
    def test_valid_input(self, mocker: MockFixture) -> None:
        mocked_nice_run = mocker.patch("opta.commands.push.nice_run")
        push_to_docker(
            "username",
            "password",
            "local_image:local_tag",
            REGISTRY_URL,
            "image_tag_override",
        )
        mocked_nice_run.assert_has_calls(
            [
                mocker.call(
                    [
                        "docker",
                        "login",
                        REGISTRY_URL,
                        "--username",
                        "username",
                        "--password-stdin",
                    ],
                    input=b"password",
                ),
                mocker.call(
                    [
                        "docker",
                        "tag",
                        "local_image:local_tag",
                        f"{REGISTRY_URL}:image_tag_override",
                    ]
                ),
                mocker.call(["docker", "push", f"{REGISTRY_URL}:image_tag_override"]),
            ]
        )

    def test_no_tag(self, mocker: MockFixture) -> None:
        with pytest.raises(Exception) as e_info:
            push_to_docker(
                "username", "password", "local_image", REGISTRY_URL, "image_tag_override"
            )

        assert (
            "Unexpected image name local_image: your image_name must be of the format <IMAGE>:<TAG>."
            in str(e_info)
        )


class TestPush:
    def test_no_docker(self, mocker: MockFixture) -> None:
        is_tool_mock = mocker.patch("opta.commands.push.is_tool")
        is_tool_mock.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["push", "local_image:local_tag"])
        print(result.exception)
        assert str(result.exception) == "Please install docker on your machine"

    def test_no_tag_override(self, mocker: MockFixture) -> None:
        nice_run_mock = mocker.patch("opta.commands.push.nice_run")
        gen_mock = mocker.patch("opta.commands.push.gen_all")
        mocker.patch(
            "opta.commands.push.get_registry_url"
        ).return_value = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"
        mocker.patch("opta.commands.push.get_ecr_auth_info").return_value = (
            "username",
            "password",
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["push", "local_image:local_tag"])

        assert result.exit_code == 0
        gen_mock.assert_called_once_with("opta.yml", None)

        nice_run_mock.assert_has_calls(
            [
                mocker.call(
                    [
                        "docker",
                        "login",
                        "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app",
                        "--username",
                        "username",
                        "--password-stdin",
                    ],
                    input=b"password",
                ),
                mocker.call(
                    [
                        "docker",
                        "tag",
                        "local_image:local_tag",
                        "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:local_tag",
                    ]
                ),
            ]
        )

    def test_with_tag_override(self, mocker: MockFixture) -> None:
        nice_run_mock = mocker.patch("opta.commands.push.nice_run")
        gen_mock = mocker.patch("opta.commands.push.gen_all")
        mocker.patch(
            "opta.commands.push.get_registry_url"
        ).return_value = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"
        mocker.patch("opta.commands.push.get_ecr_auth_info").return_value = (
            "username",
            "password",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli, ["push", "local_image:local_tag", "--tag", "tag-override"]
        )

        assert result.exit_code == 0
        gen_mock.assert_called_once_with("opta.yml", None)

        nice_run_mock.assert_has_calls(
            [
                mocker.call(
                    [
                        "docker",
                        "login",
                        "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app",
                        "--username",
                        "username",
                        "--password-stdin",
                    ],
                    input=b"password",
                ),
                mocker.call(
                    [
                        "docker",
                        "tag",
                        "local_image:local_tag",
                        "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:tag-override",
                    ]
                ),
                mocker.call(
                    [
                        "docker",
                        "push",
                        "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:tag-override",
                    ]
                ),
            ]
        )

    def test_bad_image_name(self, mocker: MockFixture) -> None:
        gen_mock = mocker.patch("opta.commands.push.gen_all")
        mocker.patch(
            "opta.commands.push.get_registry_url"
        ).return_value = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"
        mocker.patch("opta.commands.push.get_ecr_auth_info").return_value = (
            "username",
            "password",
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["push", "local_image", "--tag", "tag-override"])

        assert result.exit_code == 1
        assert (
            str(result.exception)
            == "Unexpected image name local_image: your image_name must be of the format <IMAGE>:<TAG>."
        )
        gen_mock.assert_called_once_with("opta.yml", None)
