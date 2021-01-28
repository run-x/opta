import sys

import sentry_sdk
from sentry_sdk.integrations.atexit import AtexitIntegration

if hasattr(sys, "_called_from_test"):
    print("Not sending sentry cause we think we're in a pytest")
else:

    def at_exit_callback(pending, timeout):  # type: ignore
        def echo(msg):
            # type: (str) -> None
            sys.stderr.write(msg + "\n")

        if pending > 0:
            echo("Sentry is attempting to send %i pending error messages" % pending)
            echo("Waiting up to %s seconds" % timeout)
            echo("Press Ctrl-%s to quit" % (os.name == "nt" and "Break" or "C"))
        sys.stderr.flush()

    sentry_sdk.init(
        "https://aab05facf13049368d749e1b30a08b32@o511457.ingest.sentry.io/5610510",
        traces_sample_rate=1.0,
        integrations=[AtexitIntegration(at_exit_callback)],
    )


import os  # noqa: E402
import os.path  # noqa: E402
import subprocess  # noqa: E402
from importlib.util import find_spec  # noqa: E402
from typing import List, Optional, Set  # noqa: E402

import boto3  # noqa: E402
import click  # noqa: E402
import yaml  # noqa: E402

from opta import gen_tf  # noqa: E402
from opta.amplitude import amplitude_client  # noqa: E402
from opta.layer import Layer  # noqa: E402
from opta.plugins.secret_manager import secret  # noqa: E402
from opta.utils import deep_merge, is_tool  # noqa: E402
from opta.version import version  # noqa: E402

DEFAULT_GENERATED_TF_FILE = "tmp-main.tf.json"
TERRAFORM_PLAN_FILE = "tf.plan"


@click.group()
def cli() -> None:
    pass


@cli.command()
def debugger() -> None:
    """The opta debugger -- to help you debug"""
    curses_spec = find_spec("_curses")
    curses_found = curses_spec is not None
    amplitude_client.send_event(amplitude_client.DEBUGGER_EVENT)

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
@click.option("--out", default=DEFAULT_GENERATED_TF_FILE, help="Generated tf file")
@click.option("--env", default=None, help="The env to use when loading the config file")
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
    env: Optional[str],
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
) -> None:
    print("The gen command is being deprecated in favor of the apply command")
    try:
        _apply(configfile, out, env, no_apply, refresh, max_block, var)
    finally:
        _cleanup()


@cli.command()
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--out", default=DEFAULT_GENERATED_TF_FILE, help="Generated tf file")
@click.option("--env", default=None, help="The env to use when loading the config file")
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
def apply(
    configfile: str,
    out: str,
    env: Optional[str],
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
) -> None:
    try:
        _apply(configfile, out, env, no_apply, refresh, max_block, var)
    finally:
        _cleanup()


def _apply(
    configfile: str,
    out: str,
    env: Optional[str],
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
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    for v in var:
        key, value = v.split("=")
        conf["meta"]["variables"][key] = value

    layer = Layer.load_from_dict(conf, env)
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
        amplitude_client.send_event(
            amplitude_client.PLAN_EVENT, event_properties={"block_idx": block_idx}
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
        amplitude_client.send_event(
            amplitude_client.APPLY_EVENT, event_properties={"block_idx": block_idx}
        )
        subprocess.run(
            ["terraform", "apply"] + targets + [TERRAFORM_PLAN_FILE], check=True
        )
        block_idx += 1


def _cleanup() -> None:
    try:
        os.remove(DEFAULT_GENERATED_TF_FILE)
        os.remove(TERRAFORM_PLAN_FILE)
    except FileNotFoundError:
        pass


# Initialize secret manager
cli.add_command(secret)

# Version command
cli.add_command(version)

if __name__ == "__main__":
    cli()
