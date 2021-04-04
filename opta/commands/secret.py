import base64
import re
from typing import Optional

import click
from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl
from opta.core.terraform import fetch_terraform_state_resources
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import fmt_msg


@click.group()
def secret() -> None:
    """Commands for manipulating secrets for a k8s service"""
    pass


@secret.command()
@click.argument("secret")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
def view(secret: str, env: Optional[str], config: str) -> None:
    """View a given secret of a k8s service"""
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.VIEW_SECRET_EVENT)
    gen_all(layer)
    if layer.cloud == "aws":
        _raise_if_no_eks_cluster_exists(layer)

    configure_kubectl(layer)
    load_kube_config()
    v1 = CoreV1Api()
    api_response = v1.read_namespaced_secret("secret", layer.name)
    if secret not in api_response.data:
        raise UserErrors(
            f"Secret {secret} was not specified for the app. You sure you set it in your yaml?"
        )

    print(base64.b64decode(api_response.data[secret]).decode("utf-8"))


@secret.command(name="list")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--config", default="opta.yml", help="Opta config file", show_default=True)
def list_command(env: Optional[str], config: str) -> None:
    """List the secrets setup for the given k8s service module"""
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.LIST_SECRETS_EVENT)
    gen_all(layer)
    if layer.cloud == "aws":
        _raise_if_no_eks_cluster_exists(layer)

    configure_kubectl(layer)
    load_kube_config()
    v1 = CoreV1Api()
    api_response = v1.read_namespaced_secret("secret", layer.name)

    for key in api_response.data:
        print(key)


@secret.command()
@click.argument("secret")
@click.argument("value")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--config", default="opta.yml", help="Opta config file", show_default=True)
def update(secret: str, value: str, env: Optional[str], config: str) -> None:
    """Update a given secret of a k8s service with a new value"""
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)

    if layer.cloud == "aws":
        _raise_if_no_eks_cluster_exists(layer)

    configure_kubectl(layer)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    patch = [{"op": "replace", "path": f"/data/{secret}", "value": secret_value}]
    load_kube_config()
    v1 = CoreV1Api()
    v1.patch_namespaced_secret("secret", layer.name, patch)

    print("Success")


def _raise_if_no_eks_cluster_exists(layer: "Layer") -> None:
    terraform_state = fetch_terraform_state_resources(layer)
    terraform_state_resources = terraform_state.keys()
    pattern = re.compile(r"^module\..+\.aws_eks_cluster\.cluster")
    eks_cluster = list(filter(pattern.match, terraform_state_resources))
    if len(eks_cluster) == 0:
        raise UserErrors(
            fmt_msg(
                """
                Cannot set/view secrets because there was no EKS cluster found in the opta state.
                ~Please make sure to create the opta environment first with *opta apply*.
                ~See the following docs: https://docs.runx.dev/docs/getting-started/#environment-creation
                """
            )
        )
