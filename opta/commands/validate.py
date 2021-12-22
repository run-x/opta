from typing import Optional

import click

from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yaml", help="Opta config file.")
@click.option(
    "-e",
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "--json-schema", default=False, help="Validate using JSON schema instead of Yamale"
)
def validate(config: str, json_schema: bool, env: Optional[str]) -> None:
    config = check_opta_file_exists(config)

    Layer.load_from_yaml(config, env, json_schema)
