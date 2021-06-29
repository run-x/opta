from os import path
from typing import Dict, Optional

import click
import yaml
from click_didyoumean import DYMGroup

from opta.commands.init_templates.environment.aws.template import awsTemplate
from opta.commands.init_templates.environment.gcp.template import gcpTemplate
from opta.commands.init_templates.service.k8s.template import k8sServiceTemplate
from opta.commands.init_templates.template import Template

EXAMPLES_DIR = path.join(path.dirname(__file__), "init_templates")


def _write_result(file_path: str, result: dict) -> None:
    print("--------------------------------------------\n")
    print(f"\n\nAbout to write to {path.relpath(file_path)}:\n")

    yaml_str = yaml.dump(result, sort_keys=False)
    print(yaml_str)

    ok = input("\n\nIs this OK? (yes) ") or "yes"
    if ok == "no":
        print("Aborted")
        return
    file = open(file_path, "w")
    file.write(yaml_str)


@click.group(cls=DYMGroup)
def init() -> None:
    """
    This command initializes an opta configuration file. You can create an environment
    configuration file by using the command `opta init env <cloud-provider>` and a service
    file by using the command `opta init service <environment_file> <template_name>`.

    In order to see the full list of available templates, you can
    run `opta init env --help` or `opta init service --help` respectively.
    """
    pass


@init.command()
@click.argument("cloud_provider", type=click.Choice(["aws", "gcp"]))
@click.option(
    "-f",
    "--file-name",
    default="opta.yml",
    help="The name of the file that this command will output (defaults to opta.yml)",
)
def env(cloud_provider: Optional[str], file_name: str) -> None:
    """Creates a starting point for your opta environment configuration file."""
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

    _write_result(file_path=file_name, result=res)


SERVICE_TEMPLATES: Dict[str, Template] = {
    "k8s": k8sServiceTemplate,
}


@init.command()
@click.argument(
    "environment_file", type=click.Path(exists=True),
)
@click.argument("template_name", type=click.Choice(SERVICE_TEMPLATES.keys()))
@click.option(
    "-f",
    "--file-name",
    default="opta.yml",
    help="The name of the file that this command will output (defaults to opta.yml)",
)
def service(template_name: str, file_name: str, environment_file: Optional[str]) -> None:
    """Creates a starting point for your opta service configuration file."""
    print(
        """This utility will walk you through creating an opta configuration file.
It only covers the minimal configuration necessary to get an opta service
up and running. For instructions on how to further customize this yaml file, go
to https://docs.opta.dev/.

Press ^C at any time to quit.
    """
    )

    env_dict: Optional[dict] = None

    template = SERVICE_TEMPLATES[template_name]
    res = template.run()

    try:
        if environment_file:
            with open(environment_file) as f:
                env_dict = yaml.safe_load(f)
            if env_dict:
                res["environments"] = [
                    {
                        "name": env_dict["name"],
                        "path": path.relpath(environment_file),
                        "variables": {},
                    }
                ]
    except Exception:
        print("Unable to find or process environment file. Ignoring for now...")

    _write_result(file_name, res)
    pass
