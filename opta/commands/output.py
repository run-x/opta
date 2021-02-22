import json
from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.layer import Layer


@click.command(hidden=True)
@click.option("--config", default="opta.yml", help="Opta config file")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--include-parent",
    is_flag=True,
    default=False,
    help="Also fetch outputs from the env (parent) layer",
)
@click.option(
    "--force-init",
    is_flag=True,
    default=False,
    help="Force regenerate opta setup files, instead of using cache",
)
def output(
    config: str, env: Optional[str], include_parent: bool, force_init: bool,
) -> None:
    """ Print TF outputs """
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    outputs = get_terraform_outputs()
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)
