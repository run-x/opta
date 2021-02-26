import base64
from typing import Optional, Tuple

import boto3
import click
from botocore.config import Config

from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import is_tool


def get_push_tag(local_image: str, tag_override: Optional[str]) -> str:
    if ":" not in local_image:
        raise Exception(
            f"Unexpected image name {local_image}: your image_name must be of the format <IMAGE>:<TAG>."
        )
    local_image_tag = local_image.split(":")[1]
    return tag_override or local_image_tag


def get_registry_url() -> str:
    outputs = get_terraform_outputs()
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
    )
    nice_run(["docker", "tag", local_image, remote_image_name])
    nice_run(["docker", "push", remote_image_name])


@click.command()
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
    _push(image, config, env, tag)


def _push(image: str, config: str, env: Optional[str], tag: Optional[str]) -> None:
    if not is_tool("docker"):
        raise Exception("Please install docker on your machine")
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    registry_url = get_registry_url()
    username, password = get_ecr_auth_info(layer)
    push_to_docker(username, password, image, registry_url, tag)
