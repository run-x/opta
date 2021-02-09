import os
import json
from typing import Optional, Tuple
from opta.nice_subprocess import nice_run  # noqa: E402
from opta.layer import Layer

import base64
import boto3
from botocore.config import Config


def get_registry_url() -> None:  
    print("HELLO")
    if not os.path.isdir(".terraform"):
        nice_run(["terraform", "init"], check=True)
    print("DONE")
    
    nice_run(["terraform", "get", "--update"], check=True)
    tf_output = nice_run(["terraform", "output", "-json"], check=True, capture_output=True)
    output_json = json.loads(tf_output.stdout)
    return output_json["docker_repo_url"]["value"]
  
def get_ecr_auth_info(configfile: str, env: str) -> Tuple[str, str]:
    layer = Layer.load_from_yaml(configfile, env)
    providers = layer.gen_providers(0, True)
    account_id = providers["provider"]["aws"]["allowed_account_ids"][0]
    region = providers["provider"]["aws"]["region"]
    ecr = boto3.client("ecr", config=Config(
        region_name=region
    ))
    response = ecr.get_authorization_token(
        registryIds=[
            str(account_id)
        ],
    )

    auth_info=response["authorizationData"][0]["authorizationToken"]
    decoded_auth = base64.b64decode(auth_info, altchars=None, validate=False).decode("ascii")
    username, password = decoded_auth.split(":")
    return (username, password)

def push_to_docker(username: str, password: str, local_image: str, registry_url: str, image_tag_override: Optional[str]) -> None:         
    local_image_tag = local_image.split(":")[1]
    image_tag = image_tag_override or local_image_tag
    remote_image_name = f"{registry_url}:{image_tag}"
    nice_run(["docker", "login", registry_url, "--username", username, "--password-stdin"], input=password)
    nice_run(["docker", "tag", local_image, remote_image_name])
