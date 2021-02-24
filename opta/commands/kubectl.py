from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl as configure
from opta.layer import Layer


@click.command()
@click.option("--config", default="opta.yml", help="Opta config file", show_default=True)
@click.option("--env", default=None, help="The env to use when loading the config file")
def configure_kubectl(config: str, env: Optional[str]) -> None:
    """ Configure the kubectl CLI tool for the given cluster """
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)

    configure(layer)
