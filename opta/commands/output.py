import json
from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.layer import Layer


@click.command()
@click.option("--config", default="opta.yml", help="Opta config file")
@click.option("--env", default=None, help="The env to use when loading the config file")
def output(config: str, env: Optional[str],) -> None:
    """ Print TF outputs """
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    outputs = get_terraform_outputs()
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)
