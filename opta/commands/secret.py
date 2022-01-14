from typing import Optional

import click
from click_didyoumean import DYMGroup

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import (
    configure_kubectl,
    create_namespace_if_not_exists,
)
from opta.core.secrets import get_secrets, update_manual_secrets
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.group(cls=DYMGroup)
def secret() -> None:
    """Commands for manipulating secrets for a k8s service

    Examples:

    opta secret list -c my-service.yaml

    opta secret update -c my-service.yaml "MY_SECRET_1" "value"

    opta secret view -c my-service.yaml "MY_SECRET_1"
    """
    pass


@secret.command()
@click.argument("secret")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
def view(secret: str, env: Optional[str], config: str) -> None:
    """View a given secret of a k8s service

    Examples:
    
    opta secret view -c my-service.yaml "MY_SECRET_1"
    """

    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.VIEW_SECRET_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)

    configure_kubectl(layer)
    create_namespace_if_not_exists(layer.name)
    secrets = get_secrets(layer.name)
    if secret not in secrets:
        raise UserErrors(
            f"We couldn't find a secret named {secret}. You either need to add it to your opta.yaml file or if it's"
            f" already there - update it via secret update."
        )

    print(secrets[secret])


@secret.command(name="list")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
def list_command(env: Optional[str], config: str) -> None:
    """List the secrets setup for the given k8s service module

    Examples:
    
    opta secret list -c my-service.yaml
    """
    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.LIST_SECRETS_EVENT)
    gen_all(layer)

    configure_kubectl(layer)
    create_namespace_if_not_exists(layer.name)
    secrets = get_secrets(layer.name)
    for key in secrets:
        print(key)


@secret.command()
@click.argument("secret")
@click.argument("value")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
def update(secret: str, value: str, env: Optional[str], config: str) -> None:
    """Update a given secret of a k8s service with a new value

    Examples:

    opta secret update -c my-service.yaml "MY_SECRET_1" "value"
    """

    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)

    configure_kubectl(layer)
    create_namespace_if_not_exists(layer.name)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    update_manual_secrets(layer.name, {secret: str(value)})

    print("Success")
