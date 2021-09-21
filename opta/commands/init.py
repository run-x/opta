from os import path
from typing import Dict

import click
import yaml
from click_didyoumean import DYMGroup

from opta.commands.init_templates.environment.aws.template import awsTemplate
from opta.commands.init_templates.environment.azure.template import azureTemplate
from opta.commands.init_templates.environment.gcp.template import gcpTemplate
from opta.commands.init_templates.service.k8s.template import k8sServiceTemplate
from opta.commands.init_templates.template import Template
from opta.exceptions import UserErrors

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
    try: 
        with open(file_path, "x") as f:
            file.write(yaml_str)
    except FileExistsError as e:
        raise UserErrors(f"Output file {file_path} already exists, please select another output path")


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


ENVIRONMENT_TEMPLATES: Dict[str, Template] = {
    "aws": awsTemplate,
    "gcp": gcpTemplate,
    "azure": azureTemplate,
}


@init.command()
@click.argument("cloud_provider", type=click.Choice(ENVIRONMENT_TEMPLATES.keys()))
@click.option(
    "-f",
    "--file-name",
    default="env.yml",
    help="The name of the file that this command will output (defaults to opta.yml)",
)
def env(cloud_provider: str, file_name: str) -> None:
    """Creates a starting point for your opta environment configuration file."""
    print(
        """This utility will walk you through creating an opta configuration file.
It only covers the minimal configuration necessary to get an opta environment
up and running. For instructions on how to further customize this yaml file, go
to https://docs.opta.dev/.

Press ^C at any time to quit.
    """
    )

    template = ENVIRONMENT_TEMPLATES[cloud_provider]
    res = template.run()

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
    default="service.yml",
    help="The name of the file that this command will output (defaults to opta.yml)",
)
def service(template_name: str, file_name: str, environment_file: str) -> None:
    """Creates a starting point for your opta service configuration file."""
    print(
        """This utility will walk you through creating an opta configuration file.
It only covers the minimal configuration necessary to get an opta service
up and running. For instructions on how to further customize this yaml file, go
to https://docs.opta.dev/.

Press ^C at any time to quit.
    """
    )
    with open(environment_file) as f:
        env_dict = yaml.safe_load(f)
        if not env_dict.get("name"):
            raise UserErrors("Environment file is missing a name.")

        template = SERVICE_TEMPLATES[template_name]
        res = template.run()
        if env_dict:
            res["environments"] = [
                {
                    "name": env_dict["name"],
                    "path": path.relpath(environment_file),
                    "variables": {},
                }
            ]

    _write_result(file_name, res)
    pass
