import base64
import json
import os
import subprocess
from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.layer import Layer
from opta.module import Module
from opta.utils import is_tool


@click.group()
def secret() -> None:
    pass


def get_module(app: str, secret: str, env: Optional[str], configfile: str) -> Module:
    if not is_tool("kubectl"):
        raise Exception("Please install kubectl on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    layer = Layer.load_from_yaml(configfile, env)

    target_module = None
    for block in layer.blocks:
        for module in block.modules:
            if module.key == app:
                if "secrets" in module.data and secret in module.data["secrets"]:
                    target_module = module
                    break

    if not target_module:
        raise Exception("Secret not found")
    else:
        return target_module


@secret.command()
@click.argument("app")
@click.argument("secret")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def view(app: str, secret: str, env: Optional[str], configfile: str) -> None:
    target_module = get_module(app, secret, env, configfile)
    amplitude_client.send_event(amplitude_client.VIEW_SECRET_EVENT)

    output = subprocess.run(
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


@secret.command()
@click.argument("app")
@click.argument("secret")
@click.argument("value")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def update(
    app: str, secret: str, value: str, env: Optional[str], configfile: str
) -> None:
    target_module = get_module(app, secret, env, configfile)
    amplitude_client.send_event(amplitude_client.UPDATE_SECRET_EVENT)
    secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    patch = [{"op": "replace", "path": f"/data/{secret}", "value": secret_value}]

    ret = subprocess.run(
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
