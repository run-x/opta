import os
import subprocess
from typing import Any

import click
import yaml

from os import path
from opta import gen_tf
from opta.module import Layer, Module, BACKEND_ENABLED, BACKEND_DISABLED, WAIT
from opta.plugins.link_processor import LinkProcessor
from opta.utils import deep_merge, is_tool


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.pass_context
@click.option("--inp", default="opta.yml", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
@click.option("--init", is_flag=True, default=False, help="Generate init tf file")
def apply(ctx: Any, inp: str, out: str, init: bool) -> None:
    ctx.forward(gen)
    subprocess.run(["terraform", "init"], check=True)
    subprocess.run(["terraform", "apply"], check=True)


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

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    lockdata = (
        yaml.load(open(lockfile), Loader=yaml.Loader) if path.exists(lockfile) else dict()
    )

    meta = conf.pop("meta")
    if "parent" in meta:
        if not os.path.exists(meta["parent"]):
            raise Exception(f"Parent {meta['parent']} not found")
        print(f"Identified parent {meta['parent']}")

        parent_conf = yaml.load(open(meta["parent"]), Loader=yaml.Loader)
        parent_meta = parent_conf.pop("meta")

        layer = Layer(parent_meta, parent_conf, child_meta=meta)
    else:
        layer = Layer(meta, conf)
    backend_enabled = True
    modules_data = conf["modules"] + [WAIT]
    print("Loading infra blocks")
    current_modules_data = []
    block_idx = 1
    for idx, module_data in enumerate(modules_data):
        if module_data == WAIT:
            current_module_names = list(
                map(lambda x: list(x.keys())[0], current_modules_data)
            )
            if len(current_modules_data) == 0:
                continue
            if current_module_names == lockdata.get(
                "modules_processed"
            ) and idx + 1 != len(modules_data):
                block_idx += 1
                continue
            print(f"Generating block {block_idx} for modules {current_module_names}...")
            ret = layer.gen_providers(backend_enabled)
            modules = list(
                map(
                    lambda current_module_data: Module(
                        meta,
                        list(current_module_data.keys())[0],
                        list(current_module_data.values())[0],
                        layer,
                    ),
                    current_modules_data,
                )
            )
            LinkProcessor().process(modules)

            for module in modules:
                ret = deep_merge(module.gen_blocks(), ret)

            gen_tf.gen(ret, out)
            click.confirm(
                "Will now initialize generate terraform plan for block {block_idx}. Sounds good?",
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
            lockdata["modules_processed"] = current_module_names

            print("Writing lockfile...")
            with open(lockfile, "w") as f:
                f.write(yaml.dump(lockdata))
            block_idx += 1
        elif module_data == BACKEND_ENABLED:
            print("Enabling backend")
            backend_enabled = True
        elif module_data == BACKEND_DISABLED:
            print("Disabling backend")
            backend_enabled = False
        else:
            current_modules_data.append(module_data)


if __name__ == "__main__":
    cli()
