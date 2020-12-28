import os

import click
import yaml

MODULES_DIR = os.environ.get("OPTA_MODULES_DIR")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--file", default="opta.yml", help="Opta config file")
def gen(file: str) -> None:
    """ Generate TF file based on opta config file """
    if not os.path.exists(file):
        raise Exception(f"File {file} not found")

    conf = yaml.load(open(file), Loader=yaml.Loader)

    print(conf)


if __name__ == "__main__":
    cli()
