import click

local_option = click.option(
    "--local",
    is_flag=True,
    default=False,
    help="""Use the local Kubernetes cluster for development and testing, irrespective of the environment specified inside the opta service yaml file""",
    hidden=False,
)
