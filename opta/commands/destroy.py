from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.core.terraform import Terraform
from opta.layer import Layer


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
def destroy(config: str, env: Optional[str]) -> None:
    """Destroy all opta resources from the current config"""
    amplitude_client.send_event(amplitude_client.DESTROY_EVENT)
    layer = Layer.load_from_yaml(config, env)
    Terraform.rollback(layer)
