from os import path
from typing import Optional

import click
import yaml
from click_didyoumean import DYMGroup

from opta.commands.init_templates.environment.aws.template import awsTemplate
from opta.commands.init_templates.environment.gcp.template import gcpTemplate

EXAMPLES_DIR = path.join(path.dirname(__file__), "init_templates")


@click.group(cls=DYMGroup)
def init() -> None:
    """Commands for creating an initial opta file"""
    pass


@init.command()
@click.argument("cloud_provider", type=click.Choice(["aws", "gcp"]))
@click.option(
    "-n",
    "--name",
    default="opta.yaml",
    help="The name of the file that this command will output",
)
def env(cloud_provider: Optional[str], name: str) -> None:
    print(
        """This utility will walk you through creating an opta configuration file.
It only covers the minimal configuration necessary to get an opta environment
up and running. For instructions on how to further customize this yaml file, go
to https://docs.opta.dev/.

Press ^C at any time to quit.
    """
    )

    if cloud_provider == "aws":
        res = awsTemplate.run()
    else:
        res = gcpTemplate.run()

    print(f"\n\nAbout to write to {name}:\n")

    yaml_str = yaml.dump(res, sort_keys=False)
    print(yaml_str)

    ok = input("\n\nIs this OK? (yes) ") or "yes"
    if ok == "no":
        print("Aborted")
        return
    file = open(name, "w")
    file.write(yaml_str)


@init.command()
@click.option(
    "-t", "--template", default=None, help="The opta template you would like to use"
)
@click.option(
    "-n",
    "--name",
    default="opta.yaml",
    help="The name of the file that this command will output",
)
def service(template: Optional[str], name: Optional[str]) -> None:
    print("initializing service file")
