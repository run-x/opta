import base64
from typing import Dict, Optional, Tuple

import boto3
import click
from botocore.config import Config
from docker import from_env

from opta.amplitude import amplitude_client
from opta.core.gcp import GCP
from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import check_opta_file_exists, fmt_msg, yaml
from opta.utils.clickoptions import config_option, env_option, input_variable_option
from opta.utils.dependencies import ensure_installed


def get_push_tag(local_image: str, tag_override: Optional[str]) -> str:
    if ":" not in local_image:
        raise Exception(
            f"Unexpected image name {local_image}: your image_name must be of the format <IMAGE>:<TAG>."
        )
    local_image_tag = local_image.split(":")[1]
    return tag_override or local_image_tag


def get_image_digest(registry_url: str, image_tag: str) -> str:
    docker_client = from_env()
    current_image = docker_client.images.get(f"{registry_url}:{image_tag}")
    current_digest: str
    for current_digest in current_image.attrs["RepoDigests"]:
        if current_digest.startswith(registry_url):
            return current_digest.split("@")[1]

    raise UserErrors(
        "\n"
        "|------------------------------ERROR------------------------------|\n"
        "| Unable to find the Digest for the Image Tag provided.           |\n"
        "|------------------------------ERROR------------------------------|"
    )


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


def get_acr_auth_info(layer: Layer) -> Tuple[str, str]:
    acr_name = get_terraform_outputs(layer.root()).get("acr_name")
    if acr_name is None:
        raise Exception("Could not find acr_name")
    token = nice_run(
        [
            "az",
            "acr",
            "login",
            "--name",
            acr_name,
            "--expose-token",
            "--output",
            "tsv",
            "--query",
            "accessToken",
        ],
        check=True,
        capture_output=True,
    ).stdout
    return "00000000-0000-0000-0000-000000000000", token


def push_to_docker(
    username: str,
    password: str,
    local_image: str,
    registry_url: str,
    image_tag_override: Optional[str],
) -> Tuple[str, str]:
    image_tag = get_push_tag(local_image, image_tag_override)
    remote_image_name = f"{registry_url}:{image_tag}"
    nice_run(
        ["docker", "login", registry_url, "--username", username, "--password-stdin"],
        input=password.encode(),
        check=True,
    )
    nice_run(["docker", "tag", local_image, remote_image_name], check=True)
    nice_run(["docker", "push", remote_image_name], check=True)
    return get_image_digest(registry_url, image_tag), image_tag


def push_to_docker_local(
    local_image: str, registry_url: str, image_tag_override: Optional[str],
) -> Tuple[str, str]:
    image_tag = get_push_tag(local_image, image_tag_override)
    remote_image_name = f"{registry_url}:{image_tag}"
    nice_run(["docker", "tag", local_image, remote_image_name], check=True)
    nice_run(["docker", "push", remote_image_name], check=True)
    return get_image_digest(registry_url, image_tag), image_tag


# Check if the config file is for a service or environment opta layer.
# Some commands (like push/deploy) are meant only for service layers.
#
# If the config file has the "environments" field, then it is a child/service layer.
def is_service_config(config: str) -> bool:
    with open(config) as f:
        config_data = yaml.load(f)
    return "environments" in config_data


@click.command(hidden=True)
@click.argument("image")
@config_option
@env_option
@input_variable_option
@click.option(
    "--tag",
    default=None,
    help="The image tag associated with your docker container. Defaults to your local image tag.",
)
def push(
    image: str, config: str, env: Optional[str], tag: Optional[str], var: Dict[str, str],
) -> None:
    config = check_opta_file_exists(config)
    if not is_service_config(config):
        raise UserErrors(
            fmt_msg(
                """
            Opta push can only run on service yaml files. This is an environment yaml file.
            ~See https://docs.runx.dev/docs/reference/modules/ for more details.
            ~
            ~(We know that this is an environment yaml file, because service yaml must
            ~specify the "environments" field).
            """
            )
        )

    push_image(image, config, env, tag, var)


def push_image(
    image: str, config: str, env: Optional[str], tag: Optional[str], input_variables: Dict
) -> Tuple[str, str]:
    ensure_installed("docker")
    layer = Layer.load_from_yaml(config, env, input_variables=input_variables)
    amplitude_client.send_event(
        amplitude_client.PUSH_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)
    registry_url = get_registry_url(layer)
    if layer.cloud == "aws":
        username, password = get_ecr_auth_info(layer)
    elif layer.cloud == "google":
        username, password = get_gcr_auth_info(layer)
    elif layer.cloud == "azurerm":
        username, password = get_acr_auth_info(layer)
    else:
        if layer.cloud == "local":
            return push_to_docker_local(image, registry_url, tag)
        raise Exception(f"No support for pushing image to provider {layer.cloud}")
    return push_to_docker(username, password, image, registry_url, tag)
