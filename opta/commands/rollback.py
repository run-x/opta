from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer


# Rollback automatically runs when terraform apply fails.
# This explicit command for rollback is primarily for debugging/development.
@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
def rollback(config: str, env: Optional[str]) -> None:
    """Destroy any stale opta resources in the current layer"""
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    Terraform.rollback(layer)
