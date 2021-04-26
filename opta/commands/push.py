import base64
import re
from typing import Optional, Tuple

import boto3
import click
import yaml
from botocore.config import Config

from opta.amplitude import amplitude_client
from opta.core.gcp import GCP
from opta.core.generator import gen_all
from opta.core.terraform import fetch_terraform_state_resources, get_terraform_outputs
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import fmt_msg, is_tool


def get_push_tag(local_image: str, tag_override: Optional[str]) -> str:
    if ":" not in local_image:
        raise Exception(
            f"Unexpected image name {local_image}: your image_name must be of the format <IMAGE>:<TAG>."
        )
    local_image_tag = local_image.split(":")[1]
    return tag_override or local_image_tag


def get_registry_url(layer: Layer) -> str:
    outputs = get_terraform_outputs(layer)
    if "docker_repo_url" not in outputs:
        raise Exception(
            "Unable to determine docker repository url. There is likely something wrong with your opta configuration."
        )

    return outputs["docker_repo_url"]


def get_ecr_auth_info(layer: Layer) -> Tuple[str, str]:
    providers = layer.gen_providers(0)
    account_id = providers["provider"]["aws"]["allowed_account_ids"][0]
    region = providers["provider"]["aws"]["region"]

    try:
        ecr = boto3.client("ecr", config=Config(region_name=region))
        response = ecr.get_authorization_token(registryIds=[str(account_id)],)
    except Exception:
        raise Exception(
            f"Error getting authorization token for accountId {account_id} in region {region}"
        )

    auth_info = response["authorizationData"][0]["authorizationToken"]
    decoded_auth = base64.b64decode(auth_info, altchars=None, validate=False).decode(
        "ascii"
    )
    username, password = decoded_auth.split(":")
    return username, password


def get_gcr_auth_info(layer: Layer) -> Tuple[str, str]:
    if GCP.using_service_account():
        service_account_key = GCP.get_service_account_raw_credentials()
        return "_json_key", service_account_key

    credentials, _ = GCP.get_credentials()
    return "oauth2accesstoken", credentials.token


def push_to_docker(
    username: str,
    password: str,
    local_image: str,
    registry_url: str,
    image_tag_override: Optional[str],
) -> None:
    image_tag = get_push_tag(local_image, image_tag_override)
    remote_image_name = f"{registry_url}:{image_tag}"
    nice_run(
        ["docker", "login", registry_url, "--username", username, "--password-stdin"],
        input=password.encode(),
        check=True,
    )
    nice_run(["docker", "tag", local_image, remote_image_name], check=True)
    nice_run(["docker", "push", remote_image_name], check=True)


# Check if the config file is for a service or environment opta layer.
# Some commands (like push/deploy) are meant only for service layers.
#
# If the config file has the "environments" field, then it is a child/service layer.
def is_service_config(config: str) -> bool:
    config_data = yaml.load(open(config), Loader=yaml.Loader)
    return "environments" in config_data


@click.command(hidden=True)
@click.argument("image")
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@click.option(
    "--tag",
    default=None,
    help="The image tag associated with your docker container. Defaults to your local image tag.",
)
def push(image: str, config: str, env: Optional[str], tag: Optional[str]) -> None:
    if not is_service_config(config):
        raise UserErrors(
            fmt_msg(
                """
            Opta push can only run on service yaml files. This is an environment yaml file.
            ~See https://docs.runx.dev/docs/reference/service_modules/ for more details.
            ~
            ~(We know that this is an environment yaml file, because service yaml must
            ~specify the "environments" field).
            """
            )
        )

    amplitude_client.send_event(amplitude_client.PUSH_EVENT)
    _push(image, config, env, tag)


def _push(image: str, config: str, env: Optional[str], tag: Optional[str]) -> None:
    if not is_tool("docker"):
        raise Exception("Please install docker on your machine")
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    _raise_if_no_ecr_repo_exists(layer)
    registry_url = get_registry_url(layer)
    if layer.cloud == "aws":
        username, password = get_ecr_auth_info(layer)
    elif layer.cloud == "google":
        username, password = get_gcr_auth_info(layer)
    else:
        raise Exception(f"No support for pushing image to provider {layer.cloud}")
    push_to_docker(username, password, image, registry_url, tag)


def _raise_if_no_ecr_repo_exists(layer: "Layer") -> None:
    terraform_state = fetch_terraform_state_resources(layer)
    terraform_state_resources = terraform_state.keys()

    if layer.cloud == "aws":
        pattern = re.compile(
            # Example pattern:
            # module.app.data.aws_ecr_image.service_image[0]
            r"^module\..+\.aws_ecr_image\.service_image.*"
        )
    elif layer.cloud == "google":
        pattern = re.compile(
            # Example pattern:
            # module.gcpk8sservice.data.google_container_registry_repository.root
            r"module\..+\.google_container_registry_repository.*"
        )
    else:
        # Don't fail if the cloud vendor is not supported in this check.
        return

    image_repo = list(filter(pattern.match, terraform_state_resources))
    if len(image_repo) == 0:
        raise UserErrors(
            fmt_msg(
                """
                Cannot push image because there was no image repository found in the opta state.
                ~Please make sure to create the opta service first with *opta apply*.
                ~See the following docs: https://docs.runx.dev/docs/getting-started/#service-creation
                """
            )
        )
