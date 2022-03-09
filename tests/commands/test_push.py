import base64
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import cli
from opta.commands.push import (
    get_acr_auth_info,
    get_ecr_auth_info,
    get_gcr_auth_info,
    get_registry_url,
    push_to_docker,
)
from opta.exceptions import UserErrors
from opta.layer import Layer
from tests.fixtures.basic_apply import BASIC_APPLY

REGISTRY_URL = "889760294590.dkr.ecr.us-east-1.amazonaws.com/test-service-runx-app"
TERRAFORM_OUTPUTS = {"docker_repo_url": REGISTRY_URL}


@pytest.fixture(scope="module", autouse=True)
def mock_is_service_config(module_mocker: MockFixture) -> None:
    module_mocker.patch("opta.commands.push.is_service_config", return_value=True)


def test_is_env_config(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    mocker.patch("opta.commands.push.is_service_config", return_value=False)
    runner = CliRunner()
    result = runner.invoke(cli, ["push", "local_image:local_tag"])
    assert "Opta push can only run on service yaml files." in str(result.exception)


def test_get_registry_url(mocker: MockFixture) -> None:
    mocker.patch(
        "opta.commands.push.get_terraform_outputs", return_value=TERRAFORM_OUTPUTS
    )
    layer = mocker.Mock(spec=Layer)
    layer.name = "blah"

    docker_repo_url = get_registry_url(layer)
    assert docker_repo_url == REGISTRY_URL


def test_no_docker_repo_url_in_output(mocker: MockFixture) -> None:
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("opta.commands.push.get_terraform_outputs", return_value={})
    layer = mocker.Mock(spec=Layer)
    layer.name = "blah"
    with pytest.raises(Exception) as e_info:
        get_registry_url(layer)

    expected_error_output = "Unable to determine docker repository url"
    assert expected_error_output in str(e_info)


def test_get_ecr_auth_info(mocker: MockFixture) -> None:
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.gen_providers = lambda x: BASIC_APPLY[1]

    mocked_ecr_client = mocker.Mock()

    def mock_get_authorization_token(registryIds: List[str]) -> Dict[str, Any]:
        decoded_auth_token = "username:password"
        auth_token_bytes = decoded_auth_token.encode()
        b64_auth_token = base64.b64encode(auth_token_bytes)
        return {"authorizationData": [{"authorizationToken": b64_auth_token}]}

    mocked_ecr_client.get_authorization_token = mock_get_authorization_token
    patched_boto_client = mocker.patch("opta.commands.push.boto3.client")
    patched_boto_client.return_value = mocked_ecr_client
    assert get_ecr_auth_info(mocked_layer) == ("username", "password",)


def test_get_gcr_auth_info(mocker: MockFixture) -> None:
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_credentials = mocker.Mock()
    mocked_credentials.token = "blah"
    mocker.patch("opta.commands.push.GCP.using_service_account", return_value=False)
    patched_gcp = mocker.patch(
        "opta.commands.push.GCP.get_credentials",
        return_value=tuple([mocked_credentials, "oauth2accesstoken"]),
    )
    assert get_gcr_auth_info(mocked_layer) == ("oauth2accesstoken", "blah",)
    patched_gcp.assert_called_once_with()


def test_get_acr_auth_info(mocker: MockFixture) -> None:
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.root.return_value = mocked_layer
    mocked_get_terraform_output = mocker.patch(
        "opta.commands.push.get_terraform_outputs", return_value={"acr_name": "blah"}
    )
    mocked_nice_run_output = mocker.Mock()
    mocked_nice_run = mocker.patch(
        "opta.commands.push.nice_run", return_value=mocked_nice_run_output
    )
    mocked_nice_run_output.stdout = "dummy_token"

    assert get_acr_auth_info(mocked_layer) == (
        "00000000-0000-0000-0000-000000000000",
        "dummy_token",
    )
    mocked_get_terraform_output.assert_called_once_with(mocked_layer)
    mocked_nice_run.assert_has_calls(
        [
            mocker.call(
                [
                    "az",
                    "acr",
                    "login",
                    "--name",
                    "blah",
                    "--expose-token",
                    "--output",
                    "tsv",
                    "--query",
                    "accessToken",
                ],
                check=True,
                capture_output=True,
            ),
        ]
    )


def test_valid_input(mocker: MockFixture) -> None:
    mocker.patch("opta.commands.push.get_image_digest")
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
                check=True,
            ),
            mocker.call(
                [
                    "docker",
                    "tag",
                    "local_image:local_tag",
                    f"{REGISTRY_URL}:image_tag_override",
                ],
                check=True,
            ),
            mocker.call(
                ["docker", "push", f"{REGISTRY_URL}:image_tag_override"], check=True,
            ),
        ]
    )


def test_no_tag(mocker: MockFixture) -> None:
    with pytest.raises(Exception) as e_info:
        push_to_docker(
            "username", "password", "local_image", REGISTRY_URL, "image_tag_override"
        )

    assert (
        "Unexpected image name local_image: your image_name must be of the format <IMAGE>:<TAG>."
        in str(e_info)
    )


def test_no_docker(mocker: MockFixture) -> None:
    mocker.patch(
        "opta.utils.os.path.exists", return_value=True
    )  # Make check_opta_file_exists succeed
    mocker.patch("opta.commands.push.ensure_installed", side_effect=UserErrors("foobar"))

    runner = CliRunner()
    result = runner.invoke(cli, ["push", "local_image:local_tag"])
    assert str(result.exception) == "foobar"


def test_no_tag_override(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    nice_run_mock = mocker.patch("opta.commands.push.nice_run")
    gen_mock = mocker.patch("opta.commands.push.gen_all")
    layer_object_mock = mocker.patch("opta.commands.push.Layer")
    layer_mock = mocker.Mock(spec=Layer)
    layer_mock.cloud = "aws"
    layer_mock.org_name = "dummy_org_name"
    layer_mock.name = "dummy_name"
    layer_object_mock.load_from_yaml.return_value = layer_mock
    mocker.patch(
        "opta.commands.push.get_registry_url"
    ).return_value = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"
    mocker.patch("opta.commands.push.get_ecr_auth_info").return_value = (
        "username",
        "password",
    )
    mocker.patch("opta.commands.push.get_image_digest")

    runner = CliRunner()
    result = runner.invoke(cli, ["push", "local_image:local_tag"])

    assert result.exit_code == 0
    layer_object_mock.load_from_yaml.assert_called_once_with(
        "opta.yaml", None, input_variables={}
    )
    gen_mock.assert_called_once_with(layer_mock)

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
                check=True,
            ),
            mocker.call(
                [
                    "docker",
                    "tag",
                    "local_image:local_tag",
                    "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:local_tag",
                ],
                check=True,
            ),
        ]
    )


def test_with_tag_override(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    nice_run_mock = mocker.patch("opta.commands.push.nice_run")
    gen_mock = mocker.patch("opta.commands.push.gen_all")
    layer_object_mock = mocker.patch("opta.commands.push.Layer")
    layer_mock = mocker.Mock(spec=Layer)
    layer_mock.cloud = "aws"
    layer_mock.org_name = "dummy_org_name"
    layer_mock.name = "dummy_name"
    layer_object_mock.load_from_yaml.return_value = layer_mock
    mocker.patch(
        "opta.commands.push.get_registry_url"
    ).return_value = "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app"
    mocker.patch("opta.commands.push.get_ecr_auth_info").return_value = (
        "username",
        "password",
    )
    mocker.patch("opta.commands.push.get_image_digest")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["push", "local_image:local_tag", "--tag", "tag-override"]
    )

    assert result.exit_code == 0
    layer_object_mock.load_from_yaml.assert_called_once_with(
        "opta.yaml", None, input_variables={}
    )
    gen_mock.assert_called_once_with(layer_mock)

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
                check=True,
            ),
            mocker.call(
                [
                    "docker",
                    "tag",
                    "local_image:local_tag",
                    "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:tag-override",
                ],
                check=True,
            ),
            mocker.call(
                [
                    "docker",
                    "push",
                    "889760294590.dkr.ecr.us-east-1.amazonaws.com/github-runx-app:tag-override",
                ],
                check=True,
            ),
        ]
    )


def test_bad_image_name(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    gen_mock = mocker.patch("opta.commands.push.gen_all")
    layer_object_mock = mocker.patch("opta.commands.push.Layer")
    layer_mock = mocker.Mock(spec=Layer)
    layer_mock.cloud = "aws"
    layer_mock.org_name = "dummy_org_name"
    layer_mock.name = "dummy_name"
    layer_object_mock.load_from_yaml.return_value = layer_mock
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
    layer_object_mock.load_from_yaml.assert_called_once_with(
        "opta.yaml", None, input_variables={}
    )
    gen_mock.assert_called_once_with(layer_mock)
    assert (
        str(result.exception)
        == "Unexpected image name local_image: your image_name must be of the format <IMAGE>:<TAG>."
    )
