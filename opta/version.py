import click

from opta.constants import VERSION


@click.command()
def version() -> None:
    """Current opta version"""
    print(VERSION)
