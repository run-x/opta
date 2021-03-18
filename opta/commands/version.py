import click

from opta.constants import VERSION


@click.command(hidden=True)
def version() -> None:
    """Current opta version"""
    print(VERSION)
