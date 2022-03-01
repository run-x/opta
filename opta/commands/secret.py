from typing import Optional

import click
from click_didyoumean import DYMGroup

from opta.amplitude import amplitude_client
from opta.commands.apply import _local_setup
from opta.core.generator import gen_all
from opta.core.kubernetes import (
    create_namespace_if_not_exists,
    restart_deployments,
    set_kube_config,
)
from opta.core.secrets import (
    bulk_update_manual_secrets,
    get_secrets,
    update_manual_secrets,
)
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import local_option

env_option = click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)

config_option = click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
restart_option = click.option(
    # this flag is under the form '--no' because the default behavior is to do a restart (no flag needed)
    "--no-restart",
    is_flag=True,
    default=False,
    help="""Do not restart the deployment(s) using the secrets.
    If this flag is set, the deployment(s) will need to be restarted to have the latest secret values
    """,
    show_default=True,
)


def __restart_deployments(no_restart: bool, layer_name: str) -> None:
    restart_deployments(layer_name) if not no_restart else None


@click.group(cls=DYMGroup)
def secret() -> None:
    """Manage secrets for a service

    Examples:

    opta secret list -c my-service.yaml

    opta secret update -c my-service.yaml "MY_SECRET_1" "value"

    opta secret bulk-update -c my-service.yaml secrets.env

    opta secret view -c my-service.yaml "MY_SECRET_1"

    Documentation: https://docs.opta.dev/features/secrets/
    """
    pass


@secret.command()
@click.argument("secret")
@env_option
@config_option
@local_option
def view(secret: str, env: Optional[str], config: str, local: Optional[bool]) -> None:
    """View a given secret of a k8s service

    Examples:

    opta secret view -c my-service.yaml "MY_SECRET_1"
    """

    config = check_opta_file_exists(config)
    if local:
        config = _local_setup(config)
        env = "localopta"
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.VIEW_SECRET_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)

    set_kube_config(layer)
    create_namespace_if_not_exists(layer.name)
    secrets = get_secrets(layer.name)
    if secret not in secrets:
        raise UserErrors(
            f"We couldn't find a secret named {secret}. You either need to add it to your opta.yaml file or if it's"
            f" already there - update it via secret update."
        )

    print(secrets[secret])


@secret.command(name="list")
@env_option
@config_option
@local_option
def list_command(env: Optional[str], config: str, local: Optional[bool]) -> None:
    """List the secrets (names and values) for the given k8s service module

      It expects a file in the dotenv file format.
      Each line is in VAR=VAL format.


      The output is in the dotenv file format. Each line is in
    VAR=VAL format.

      Examples:

      opta secret list -c my-service.yaml
    """
    config = check_opta_file_exists(config)
    if local:
        config = _local_setup(config)
        env = "localopta"
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.LIST_SECRETS_EVENT)
    gen_all(layer)

    set_kube_config(layer)
    create_namespace_if_not_exists(layer.name)
    secrets = get_secrets(layer.name)
    for key, value in secrets.items():
        print(f"{key}={value}")


@secret.command()
@click.argument("secret")
@click.argument("value")
@env_option
@config_option
@restart_option
@local_option
def update(
    secret: str,
    value: str,
    env: Optional[str],
    config: str,
    no_restart: bool,
    local: Optional[bool],
) -> None:
    """Update a given secret of a k8s service with a new value

    Examples:

    opta secret update -c my-service.yaml "MY_SECRET_1" "value"
    """

    config = check_opta_file_exists(config)
    if local:
        config = _local_setup(config)
        env = "localopta"
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)

    set_kube_config(layer)
    create_namespace_if_not_exists(layer.name)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    update_manual_secrets(layer.name, {secret: str(value)})
    __restart_deployments(no_restart, layer.name)

    print("Success")


@secret.command()
@click.argument("env-file")
@env_option
@config_option
@restart_option
@local_option
def bulk_update(
    env_file: str,
    env: Optional[str],
    config: str,
    no_restart: bool,
    local: Optional[bool],
) -> None:
    """Bulk update a list of secrets for a k8s service using a dotenv file as in input.

    Each line of the file should be in VAR=VAL format.

    Examples:

    opta secret bulk-update -c my-service.yaml secrets.env
    """

    config = check_opta_file_exists(config)
    if local:
        config = _local_setup(config)
        env = "localopta"
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)

    set_kube_config(layer)
    create_namespace_if_not_exists(layer.name)
    amplitude_client.send_event(amplitude_client.UPDATE_BULK_SECRET_EVENT)

    bulk_update_manual_secrets(layer.name, env_file)
    __restart_deployments(no_restart, layer.name)

    print("Success")
