from typing import Optional

import click

from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e",
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
def validate(config: str, env: Optional[str]) -> None:
    check_opta_file_exists(config)
    Layer.load_from_yaml(config, env)
