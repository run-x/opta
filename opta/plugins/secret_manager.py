import base64
import json
import os
import subprocess
from typing import Optional

import click

from opta.layer import Layer
from opta.utils import is_tool


@click.group()
def secret() -> None:
    pass


def get_name_if_exists(secret: str, configfile: str) -> Optional[str]:
    if not is_tool("kubectl"):
        raise Exception("Please install kubectl on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    layer = Layer.load_from_yaml(configfile)
    for block in layer.blocks:
        for module in block.modules:
            if secret == module.key and module.data["type"] == "k8s-secret":
                secret_name = f"{layer.meta['name']}.{module.key}"
                return secret_name

    return None


@secret.command()
@click.option("--secret", required=True, help="Secret name")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def view(secret: str, configfile: str) -> None:
    secret_name = get_name_if_exists(secret, configfile)

    if secret_name is not None:
        output = subprocess.run(
            ["kubectl", "get", f"secrets/{secret_name}", "--template={{.data.value}}"],
            capture_output=True,
        )
        if output.returncode == 0:
            print(base64.b64decode(output.stdout).decode("utf-8"))
            return

    raise Exception("Secret not found")


@secret.command()
@click.option("--secret", required=True, help="Secret name")
@click.option("--value", required=True, help="Value")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def update(secret: str, value: str, configfile: str) -> None:
    secret_name = get_name_if_exists(secret, configfile)
    secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    patch = [{"op": "replace", "path": "/data/value", "value": secret_value}]

    if secret_name is not None:
        ret = subprocess.run(
            [
                "kubectl",
                "patch",
                "secret",
                secret_name,
                "--type=json",
                f"-p={json.dumps(patch)}",
            ]
        )
        if ret.returncode == 0:
            print("Success")
            return
        else:
            raise Exception(ret)

    raise Exception("Secret not found")
