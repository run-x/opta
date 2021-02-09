import base64
from typing import Any, Dict, List, Optional
from pytest_mock import MockFixture
from subprocess import CompletedProcess
from opta.layer import Layer
from tests.fixtures.apply import BASIC_APPLY
import pytest

import json

from opta.helpers.cli.push import get_registry_url, get_ecr_auth_info, push_to_docker

REGISTRY_URL = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"


class TestGetRegistryUrl:
    def test_terrform_directory_already_exists(self, mocker: MockFixture) -> None:  # noqa
        mocked_isdir = mocker.patch("os.path.isdir")
        mocked_isdir.return_value = True

        mocked_terraform_get = mocker.Mock(spec=CompletedProcess)
        mocked_terraform_output = mocker.Mock(spec=CompletedProcess)
        mocked_terraform_output.stdout = json.dumps({
            "docker_repo_url": {
                "sensitive": False,
                "type": "string",
                "value": REGISTRY_URL
            }
        })

        def nice_run_results(args_array: List[str], **kwargs: Any) -> Any:
            if args_array == ["terraform", "get", "--update"]:
                return mocked_terraform_get
            if args_array == ["terraform", "output", "-json"]:
                return mocked_terraform_output
            raise Exception("Unexpected test input")

        nice_run_mock = mocker.patch(
            "opta.helpers.cli.push.nice_run", side_effect=nice_run_results)

        docker_repo_url = get_registry_url()
        nice_run_mock.assert_has_calls([
            mocker.call(["terraform", "get", "--update"], check=True),
            mocker.call(["terraform", "output", "-json"], check=True, capture_output=True)
        ])
        assert docker_repo_url == REGISTRY_URL

    def test_terrform_directory_does_not_exist(self, mocker: MockFixture) -> None:  # noqa
        mocked_isdir = mocker.patch("os.path.isdir")
        mocked_isdir.return_value = False

        mocked_terraform_init = mocker.Mock(spec=CompletedProcess)
        mocked_terraform_get = mocker.Mock(spec=CompletedProcess)
        mocked_terraform_output = mocker.Mock(spec=CompletedProcess)
        mocked_terraform_output.stdout = json.dumps({
            "docker_repo_url": {
                "sensitive": False,
                "type": "string",
                "value": REGISTRY_URL
            }
        })

        def nice_run_results(args_array: List[str], **kwargs: Any) -> Any:
            if args_array == ["terraform", "init"]:
                return mocked_terraform_init
            if args_array == ["terraform", "get", "--update"]:
                return mocked_terraform_get
            if args_array == ["terraform", "output", "-json"]:
                return mocked_terraform_output
            raise Exception("Unexpected test input")

        nice_run_mock = mocker.patch(
            "opta.helpers.cli.push.nice_run", side_effect=nice_run_results)

        docker_repo_url = get_registry_url()
        nice_run_mock.assert_has_calls([
            mocker.call(["terraform", "init"], check=True),
            mocker.call(["terraform", "get", "--update"], check=True),
            mocker.call(["terraform", "output", "-json"], check=True, capture_output=True)
        ])

        assert docker_repo_url == REGISTRY_URL

class TestGetEcrAuthInfo:
    def test_get_ecr_auth_info(self, mocker: MockFixture) -> None:
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.gen_providers = lambda x, y: BASIC_APPLY[1]

        mocked_ecr_client = mocker.Mock()

        def mock_get_authorization_token(registryIds: List[str]) -> Dict[str, Any]:
            decoded_auth_token = "username:password"
            auth_token_bytes = decoded_auth_token.encode()
            b64_auth_token = base64.b64encode(auth_token_bytes)
            return {
                "authorizationData": [
                    {
                        "authorizationToken": b64_auth_token
                    }
                ]
            }
        mocked_ecr_client.get_authorization_token = mock_get_authorization_token
        patched_boto_client = mocker.patch("opta.helpers.cli.push.boto3.client")
        patched_boto_client.return_value = mocked_ecr_client

        def mocked_load_from_yaml(configfile: str, env: Optional[str]) -> Layer:
            return mocked_layer

        mocker.patch.object(Layer, "load_from_yaml", new=mocked_load_from_yaml)
        assert get_ecr_auth_info(configfile="opta.yml",
                                 env="runx-staging") == ("username", "password")

class TestPushToDocker:
    def test_valid_input(self, mocker: MockFixture) -> None:
        mocked_nice_run = mocker.patch("opta.helpers.cli.push.nice_run")
        push_to_docker("username", "password", "local_image:local_tag",
                       REGISTRY_URL, "image_tag_override")
        mocked_nice_run.assert_has_calls([
            mocker.call(["docker", "login", REGISTRY_URL, "--username",
                         "username", "--password-stdin"], input="password"),
            mocker.call(["docker", "tag", "local_image:local_tag",
                         "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:image_tag_override"]),
            mocker.call(["docker", "push", "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:image_tag_override"]),
        ])
    
    def test_no_tag(self, mocker: MockFixture) -> None:
        with pytest.raises(Exception) as e_info:
            push_to_docker("username", "password", "local_image",
                REGISTRY_URL, "image_tag_override")  
    
        assert "Unexpected image name local_image: your image_name must be of the format <IMAGE>:<TAG>." in str(e_info)