import click

from opta.constants import VERSION


@click.command()
def version() -> None:
    print(VERSION)
