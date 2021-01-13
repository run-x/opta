import os
import subprocess
from typing import Optional, Set

import click

from opta import gen_tf
from opta.layer import Layer
from opta.plugins.secret_manager import secret
from opta.utils import deep_merge, is_tool


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--out", default="main.tf.json", help="Generated tf file")
@click.option(
    "--no-apply",
    is_flag=True,
    default=False,
    help="Do not run terraform, just write the json",
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Run from first block, regardless of current state",
)
@click.option("--max-block", default=None, type=int, help="Max block to process")
def gen(
    configfile: str, out: str, no_apply: bool, refresh: bool, max_block: Optional[int]
) -> None:
    _gen(configfile, out, no_apply, refresh, max_block)


def _gen(
    configfile: str, out: str, no_apply: bool, refresh: bool, max_block: Optional[int]
) -> None:
    """ Generate TF file based on opta config file """
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    layer = Layer.load_from_yaml(configfile)
    current_module_keys: Set[str] = set()
    print("Loading infra blocks")
    blocks_to_process = layer.blocks
    if max_block is not None:
        blocks_to_process = layer.blocks[: max_block + 1]
    for block_idx, block in enumerate(blocks_to_process):
        current_module_keys = current_module_keys.union(
            set(list(map(lambda x: x.key, block.modules)))
        )
        total_modules_applied = set()
        try:
            current_state = (
                subprocess.run(
                    ["terraform", "state", "list"], check=True, capture_output=True
                )
                .stdout.decode("utf-8")
                .split("\n")
            )
            for resource in current_state:
                if resource.startswith("module"):
                    total_modules_applied.add(resource.split(".")[1])
        except Exception:
            print("Couldn't find terraform state, assuming new build.")
        if (
            current_module_keys.issubset(total_modules_applied)
            and block_idx + 1 != len(blocks_to_process)
            and not refresh
        ):
            continue
        print(f"Generating block {block_idx} for modules {current_module_keys}...")
        ret = layer.gen_providers(block_idx, block.backend_enabled)
        ret = deep_merge(layer.gen_tf(block_idx), ret)

        gen_tf.gen(ret, out)
        if no_apply:
            continue
        click.confirm(
            f"Will now initialize generate terraform plan for block {block_idx}. "
            "Sounds good?",
            abort=True,
        )
        targets = list(map(lambda x: f"-target=module.{x}", current_module_keys))
        subprocess.run(["terraform", "init"], check=True)
        subprocess.run(["terraform", "plan", "-out=tf.plan"] + targets, check=True)

        click.confirm(
            "Terraform plan generation successful, would you like to apply?", abort=True,
        )
        subprocess.run(["terraform", "apply"] + targets + ["tf.plan"], check=True)
        block_idx += 1


# Initialize secret manager
cli.add_command(secret)

if __name__ == "__main__":
    cli()
