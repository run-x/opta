from typing import TYPE_CHECKING, Dict, Tuple

import click

from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from click import Context, Parameter


def parse_variables(
    ctx: "Context", param: "Parameter", value: Tuple[str, ...]
) -> Dict[str, str]:
    output = {}
    for input in value:
        input_parts = input.split("=", 1)
        if len(input_parts) == 1:
            raise UserErrors(f"Invalid input {input}")
        output[input_parts[0]] = input_parts[1]
    return output


local_option = click.option(
    "--local",
    is_flag=True,
    default=False,
    help="""Use the local Kubernetes cluster for development and testing, irrespective of the environment specified inside the opta service yaml file""",
    hidden=False,
)

env_option = click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)

config_option = click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
input_variable_option = click.option(
    "--var",
    "-v",
    multiple=True,
    default=[],
    callback=parse_variables,
    help="Add input variables to your yaml at run time (e.g. --var variable1=value1)",
)


def str_options(ctx: click.Context) -> str:
    "print_options returns the options passed in a printable format"
    return " ".join(
        [
            f"--{key}={value}"
            for key, value in ctx.params.items()
            if value is not None and value is not False
        ]
    ).replace("=True", "")
