import os
import subprocess
from os import path

import click
import yaml

from opta import gen_tf
from opta.layer import Layer
from opta.utils import deep_merge, is_tool


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--lockfile", default="opta.lock", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
def gen(configfile: str, lockfile: str, out: str) -> None:
    """ Generate TF file based on opta config file """
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    lockdata = (
        yaml.load(open(lockfile), Loader=yaml.Loader) if path.exists(lockfile) else dict()
    )
    lockdata["blocks_processed"] = lockdata.get("blocks_processed", [])

    layer = Layer.load_from_yaml(configfile)
    block_idx = 1
    current_module_names = []
    print("Loading infra blocks")
    for idx, block in enumerate(layer.blocks):
        current_module_names += list(map(lambda x: x.name, block.modules))
        if len(lockdata["blocks_processed"]) <= idx:
            lockdata["blocks_processed"].append({"modules": []})
        if current_module_names == lockdata["blocks_processed"][idx][
            "modules"
        ] and idx + 1 != len(layer.blocks):
            block_idx += 1
            continue
        print(f"Generating block {block_idx} for modules {current_module_names}...")
        ret = layer.gen_providers(block.backend_enabled)
        ret = deep_merge(layer.gen_tf(block_idx), ret)

        gen_tf.gen(ret, out)
        click.confirm(
            "Will now initialize generate terraform plan for block {block_idx}. "
            "Sounds good?",
            abort=True,
        )
        targets = list(map(lambda x: f"-target=module.{x}", current_module_names))
        subprocess.run(["terraform", "init"], check=True)
        subprocess.run(["terraform", "plan", "-out=tf.plan"] + targets, check=True)

        click.confirm(
            "Terraform plan generation successful, would you like to apply?",
            abort=True,
        )
        subprocess.run(["terraform", "apply"] + targets + ["tf.plan"], check=True)

        lockdata["blocks_processed"][idx]["modules"] = current_module_names
        print("Writing lockfile...")
        with open(lockfile, "w") as f:
            f.write(yaml.dump(lockdata))
        block_idx += 1


if __name__ == "__main__":
    cli()
