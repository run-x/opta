import click

local_option = click.option(
    "--local",
    is_flag=True,
    default=False,
    help="""Use the local Kubernetes cluster for development and testing, irrespective of the environment specified inside the opta service yaml file""",
    hidden=False,
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
