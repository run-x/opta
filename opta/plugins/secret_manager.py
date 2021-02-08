import base64
import json
import os
from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.layer import Layer
from opta.module import Module
from opta.nice_subprocess import nice_run
from opta.utils import is_tool


@click.group()
def secret() -> None:
    """Commands for manipulating secrets for a k8s service"""
    pass


def get_module(
    module_name: str, secret: Optional[str], env: Optional[str], configfile: str
) -> Module:
    if not is_tool("kubectl"):
        raise Exception("Please install kubectl on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    layer = Layer.load_from_yaml(configfile, env)

    target_module = None
    for block in layer.blocks:
        for module in block.modules:
            if module.key == module_name:
                target_module = module
                break

    if not target_module:
        raise Exception("Secret not found")
    else:
        return target_module


@secret.command()
@click.argument("module_name")
@click.argument("secret")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def view(module_name: str, secret: str, env: Optional[str], configfile: str) -> None:
    """View a given secret of a k8s service"""
    target_module = get_module(module_name, secret, env, configfile)
    amplitude_client.send_event(amplitude_client.VIEW_SECRET_EVENT)

    output = nice_run(
        [
            "kubectl",
            "get",
            "secrets/secret",
            f"--namespace={target_module.layer_name}",
            f"--template={{{{.data.{secret}}}}}",
        ],
        capture_output=True,
    )

    if output.returncode != 0:
        raise Exception("Something went wrong")

    print(base64.b64decode(output.stdout).decode("utf-8"))


@secret.command(name="list")
@click.argument("module_name")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def list_command(module_name: str, env: Optional[str], configfile: str) -> None:
    """List the secrets setup for the given k8s service module"""
    target_module = get_module(module_name, None, env, configfile)
    amplitude_client.send_event(amplitude_client.LIST_SECRETS_EVENT)

    output = nice_run(
        [
            "kubectl",
            "get",
            "secrets/secret",
            f"--namespace={target_module.layer_name}",
            "-o",
            "jsonpath='{.data}'",
        ],
        capture_output=True,
    )

    if output.returncode != 0:
        print(output.stdout)
        print(output.returncode)
        raise Exception(f"Something went wrong, got exit code of {output.returncode}")

    for key in json.loads(output.stdout.decode("utf-8").strip("'")).keys():
        print(key)


@secret.command()
@click.argument("module_name")
@click.argument("secret")
@click.argument("value")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def update(
    module_name: str, secret: str, value: str, env: Optional[str], configfile: str
) -> None:
    """Update a given secret of a k8s service with a new value"""
    target_module = get_module(module_name, secret, env, configfile)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    patch = [{"op": "replace", "path": f"/data/{secret}", "value": secret_value}]

    ret = nice_run(
        [
            "kubectl",
            "patch",
            "secret",
            "secret",
            f"--namespace={target_module.layer_name}",
            "--type=json",
            f"-p={json.dumps(patch)}",
        ]
    )

    if ret.returncode != 0:
        raise Exception("Something went wrong")

    print("Success")
