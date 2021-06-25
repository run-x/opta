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
    print(f"About to write to {file_path}:\n")
    print("--------------------------------------------\n")

    yaml_str = yaml.dump(result, sort_keys=False)
    print(yaml_str)
    print("--------------------------------------------")

    ok = input("\n\nIs this OK? (yes) ") or "yes"
    if ok == "no":
        print("Aborted")
        return
    file = open(file_path, "w")
    file.write(yaml_str)


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

    _write_result(file_path=name, result=res)


SERVICE_TEMPLATES: Dict[str, Template] = {
    "k8s": k8sServiceTemplate,
}


@init.command()
@click.argument("template_name", type=click.Choice(SERVICE_TEMPLATES.keys()))
@click.option(
    "-n",
    "--file-name",
    default="opta.yaml",
    help="The name of the file that this command will output",
)
@click.option(
    "-e",
    "--environment-file",
    type=click.Path(exists=True),
    help="The name of the opta environment you would like to deploy this service in",
)
def service(
    template_name: Optional[str], file_name: str, environment_file: Optional[str]
) -> None:
    print(
        """This utility will walk you through creating an opta configuration file.
It only covers the minimal configuration necessary to get an opta service
up and running. For instructions on how to further customize this yaml file, go
to https://docs.opta.dev/.

Press ^C at any time to quit.
    """
    )

    env_dict: Optional[dict] = None

    template = SERVICE_TEMPLATES["k8s"]
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
