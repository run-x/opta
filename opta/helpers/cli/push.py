import base64
import json
import os
from typing import Optional, Tuple

import boto3
from botocore.config import Config

from opta.layer import Layer
from opta.nice_subprocess import nice_run  # noqa: E402
from opta.output import get_terraform_outputs

def get_registry_url() -> None:
    outputs = get_terraform_outputs()
    if (
        "docker_repo_url" not in outputs
    ):
        raise Exception(
            "Unable to determine docker repository url. There is likely something wrong with your opta configuration."
        )

    return outputs["docker_repo_url"]


def get_ecr_auth_info(configfile: str, env: str) -> Tuple[str, str]:
    layer = Layer.load_from_yaml(configfile, env)
    providers = layer.gen_providers(0, True)
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
    return (username, password)


def push_to_docker(
    username: str,
    password: str,
    local_image: str,
    registry_url: str,
    image_tag_override: Optional[str],
) -> None:
    if ":" not in local_image:
        raise Exception(
            f"Unexpected image name {local_image}: your image_name must be of the format <IMAGE>:<TAG>."
        )
    local_image_tag = local_image.split(":")[1]
    image_tag = image_tag_override or local_image_tag
    remote_image_name = f"{registry_url}:{image_tag}"
    nice_run(
        ["docker", "login", registry_url, "--username", username, "--password-stdin"],
        input=password.encode(),
    )
    nice_run(["docker", "tag", local_image, remote_image_name])
    nice_run(["docker", "push", remote_image_name])
