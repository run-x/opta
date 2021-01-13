import base64
import os
import subprocess

import click

from opta.layer import Layer
from opta.utils import is_tool


@click.group()
def secret() -> None:
    pass


@secret.command()
@click.option("--secret", required=True, help="Secret name")
@click.option("--configfile", default="opta.yml", help="Opta config file")
def view(secret: str, configfile: str) -> None:
    if not is_tool("kubectl"):
        raise Exception("Please install kubectl on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    layer = Layer.load_from_yaml(configfile)
    found = False
    for block in layer.blocks:
        for module in block.modules:
            if secret == module.key and module.data["type"] == "k8s-secret":
                secret_name = f"{layer.meta['name']}.{module.key}"
                output = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        f"secrets/{secret_name}",
                        "--template={{.data.value}}",
                    ],
                    capture_output=True,
                )
                if output.returncode == 0:
                    print(base64.b64decode(output.stdout).decode("utf-8"))
                    found = True

    if not found:
        raise Exception("Secret not found")
