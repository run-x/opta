import os
import os.path
import subprocess
from importlib.util import find_spec
from typing import List, Optional, Set

import boto3
import click
import yaml

from opta import gen_tf
from opta.layer import Layer
from opta.plugins.secret_manager import secret
from opta.utils import deep_merge, is_tool


@click.group()
def cli() -> None:
    pass


@cli.command()
def debugger() -> None:
    """The opta debugger -- to help you debug"""
    curses_spec = find_spec("_curses")
    curses_found = curses_spec is not None

    if curses_found:
        from opta.debugger import Debugger

        dbg = Debugger()
        dbg.run()
    else:
        print(
            "We're very sorry but it seems like your python installation does not "
            "support curses for advanced cli ui experience. This is a known issue if you "
            "have pyenv + Big Sur-- pls look at this issue documentations: "
            "https://github.com/pyenv/pyenv/issues/1755"
        )


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
@click.option("--var", multiple=True, default=[], type=str, help="Variable to update")
def gen(
    configfile: str,
    out: str,
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
) -> None:
    _gen(configfile, out, no_apply, refresh, max_block, var)


def _gen(
    configfile: str,
    out: str,
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
) -> None:
    """ Generate TF file based on opta config file """
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")
    if not os.path.exists(configfile):
        raise Exception(f"File {configfile} not found")

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    for v in var:
        key, value = v.split("=")
        conf["meta"]["variables"][key] = value

    layer = Layer.load_from_dict(conf)
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
            if not os.path.isdir("./.terraform") and not os.path.isfile(
                "./terraform.tfstate"
            ):
                print(
                    "Couldn't find terraform state locally, gonna check to see if remote "
                    "state is available"
                )
                providers = layer.gen_providers(0, True)
                if "s3" in providers.get("terraform", {}).get("backend", {}):
                    bucket = providers["terraform"]["backend"]["s3"]["bucket"]
                    key = providers["terraform"]["backend"]["s3"]["key"]
                    print(
                        f"Found an s3 backend in bucket {bucket} and key {key}, "
                        "gonna try to download the statefile from there"
                    )
                    s3 = boto3.client("s3")
                    s3.download_file(bucket, key, "./terraform.tfstate")
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
            print("Terraform state was unavailable, will assume a new build.")

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

        # Always fetch the latest modules while we're still in active development
        subprocess.run(["terraform", "get", "--update"], check=True)

        subprocess.run(["terraform", "init"], check=True)
        subprocess.run(["terraform", "plan", "-out=tf.plan"] + targets, check=True)

        click.confirm(
            "Terraform plan generation successful, would you like to apply?",
            abort=True,
        )
        subprocess.run(["terraform", "apply"] + targets + ["tf.plan"], check=True)
        block_idx += 1


# Initialize secret manager
cli.add_command(secret)

if __name__ == "__main__":
    cli()
