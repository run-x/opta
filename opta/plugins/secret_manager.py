import base64
from typing import Optional

import click
from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module


@click.group()
def secret() -> None:
    """Commands for manipulating secrets for a k8s service"""
    pass


def get_module(module_name: str, env: Optional[str], configfile: str) -> Module:
    layer = Layer.load_from_yaml(configfile, env)
    target_module = layer.get_module(module_name)

    if target_module is None:
        raise UserErrors(f"Invalid target module {module_name}. Not found in layer")
    else:
        return target_module


@secret.command()
@click.argument("module_name")
@click.argument("secret")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
def view(module_name: str, secret: str, env: Optional[str], configfile: str) -> None:
    """View a given secret of a k8s service"""
    target_module = get_module(module_name, env, configfile)
    amplitude_client.send_event(amplitude_client.VIEW_SECRET_EVENT)
    load_kube_config()
    v1 = CoreV1Api()
    api_response = v1.read_namespaced_secret("secret", target_module.layer_name)
    if secret not in api_response.data:
        raise UserErrors(
            f"Secret {secret} was not specified for the app. You sure you set it in your yaml?"
        )

    print(base64.b64decode(api_response.data[secret]).decode("utf-8"))


@secret.command(name="list")
@click.argument("module_name")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
def list_command(module_name: str, env: Optional[str], configfile: str) -> None:
    """List the secrets setup for the given k8s service module"""
    target_module = get_module(module_name, env, configfile)
    amplitude_client.send_event(amplitude_client.LIST_SECRETS_EVENT)

    load_kube_config()
    v1 = CoreV1Api()
    api_response = v1.read_namespaced_secret("secret", target_module.layer_name)

    for key in api_response.data:
        print(key)


@secret.command()
@click.argument("module_name")
@click.argument("secret")
@click.argument("value")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
def update(
    module_name: str, secret: str, value: str, env: Optional[str], configfile: str
) -> None:
    """Update a given secret of a k8s service with a new value"""
    target_module = get_module(module_name, env, configfile)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    patch = [{"op": "replace", "path": f"/data/{secret}", "value": secret_value}]
    load_kube_config()
    v1 = CoreV1Api()
    v1.patch_namespaced_secret("secret", target_module.layer_name, patch)

    print("Success")
