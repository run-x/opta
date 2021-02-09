import base64
from typing import Any, Dict, List, Optional
from pytest_mock import MockFixture
from subprocess import CompletedProcess
from opta.layer import Layer
from tests.fixtures.apply import BASIC_APPLY

import json

from opta.helpers.cli.push import get_registry_url, get_ecr_auth_info, push_to_docker

REGISTRY_URL = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"

class TestCliPushHelpers:
    def test_get_registry_url(self, mocker: MockFixture) -> None: #noqa
        mocked_isdir = mocker.patch("os.path.isdir")
        mocked_isdir.return_value = True
      
        mocked_completed_update = mocker.Mock(spec=CompletedProcess)
        mocked_completed_output = mocker.Mock(spec=CompletedProcess)
        mocked_completed_output.stdout = json.dumps({
            "docker_repo_url": {
                "sensitive": False,
                "type": "string",
                "value": REGISTRY_URL
            }
        })
        
        def nice_run_results(args_array: List[str], **kwargs: Any) -> Any:
            print("ARGS_ARRAY!!!")
            print(args_array)
            if args_array == ["terraform", "get", "--update"]:
              return mocked_completed_update
            if args_array == ["terraform", "output", "-json"]:
              return mocked_completed_output
            raise Exception("Unexpected test input")
        
        mocker.patch("opta.helpers.cli.push.nice_run", side_effect=nice_run_results)
        
        docker_repo_url = get_registry_url()
        assert docker_repo_url == REGISTRY_URL
        
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
        assert get_ecr_auth_info(configfile="opta.yml", env="runx-staging") == ("username", "password")
        
    def test_push_to_docker(self, mocker: MockFixture) -> None:
        mocked_nice_run = mocker.patch("opta.helpers.cli.push.nice_run")
        push_to_docker("username", "password", "local_image:local_tag", REGISTRY_URL, "image_tag_override")
        mocked_nice_run.assert_has_calls([
            mocker.call(["docker", "login", REGISTRY_URL, "--username", "username", "--password-stdin"], input="password"),
            mocker.call(["docker", "tag", "local_image:local_tag", "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:image_tag_override"]),
        ])
