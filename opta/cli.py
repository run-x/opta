import os
import os.path
import sys
from importlib.util import find_spec
from subprocess import CalledProcessError
from typing import Any, List, Optional, Set

import boto3
import click
import yaml

import opta.sentry  # noqa: F401 This leads to initialization of sentry sdk
from opta import gen_tf
from opta.amplitude import amplitude_client
from opta.commands.output import output
from opta.commands.push import push
from opta.commands.secret import secret
from opta.commands.version import version
from opta.constants import TF_FILE_PATH
from opta.exceptions import UserErrors
from opta.inspect_cmd import InspectCommand
from opta.kubectl import setup_kubectl
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import deep_merge, is_tool, logger

TERRAFORM_PLAN_FILE_PATH = "tf.plan"
TF_STATE_FILE = "terraform.tfstate"
TF_STATE_BACKUP_FILE = "terraform.tfstate.backup"


@click.group()
def cli() -> None:
    """Welcome to opta, runx's cli!"""
    pass


@cli.command(hidden=True)
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
        logger.warning(
            "We're very sorry but it seems like your python installation does not "
            "support curses for advanced cli ui experience. This is a known issue if you "
            "have pyenv + Big Sur-- pls look at this issue documentations: "
            "https://github.com/pyenv/pyenv/issues/1755"
        )


@cli.command()
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.pass_context
def inspect(ctx: Any, configfile: str, env: Optional[str]) -> None:
    """ Displays important resources and AWS/Datadog links to them """
    ctx.invoke(apply, configfile=configfile, env=env, no_apply=True)
    nice_run(["terraform", "init"], check=True)
    InspectCommand(configfile, env).run()


@cli.command()
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.pass_context
def configure_kubectl(ctx: Any, configfile: str, env: Optional[str]) -> None:
    """ Configure the kubectl CLI tool for the given cluster """
    ctx.invoke(apply, configfile=configfile, env=env, no_apply=True)
    # Also switches the current kubectl context to the cluster.
    setup_kubectl(configfile, env)


@cli.command()
@click.option(
    "--configfile", default="opta.yml", help="Opta config file", show_default=True
)
@click.option(
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "--no-apply",
    is_flag=True,
    default=False,
    help="Do not run terraform, just write the json",
    hidden=True,
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Run from first block, regardless of current state",
    hidden=True,
)
@click.option(
    "--max-block", default=None, type=int, help="Max block to process", hidden=True
)
@click.option("--var", multiple=True, default=[], type=str, help="Variable to update")
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run tf plan, but don't lock state file",
    hidden=True,
)
def apply(
    configfile: str,
    env: Optional[str],
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
    test: bool,
) -> None:
    """Apply your opta config file to your infrastructure!"""
    _apply(configfile, env, no_apply, refresh, max_block, var, test)


def _apply(
    configfile: str,
    env: Optional[str],
    no_apply: bool,
    refresh: bool,
    max_block: Optional[int],
    var: List[str],
    test: bool,
) -> None:
    """ Generate TF file based on opta config file """
    if not is_tool("terraform"):
        raise UserErrors("Please install terraform on your machine")
    if not os.path.exists(configfile):
        raise UserErrors(f"File {configfile} not found")
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    for v in var:
        key, value = v.split("=")
        conf["meta"]["variables"] = conf["meta"].get("variables", {})
        conf["meta"]["variables"][key] = value

    layer = Layer.load_from_dict(conf, env)
    current_module_keys: Set[str] = set()
    total_modules_applied: Set[str] = set()
    print("Loading infra blocks")
    blocks_to_process = (
        layer.blocks[: max_block + 1] if max_block is not None else layer.blocks
    )
    for block_idx, block in enumerate(blocks_to_process):
        current_module_keys = current_module_keys.union(
            set(map(lambda x: x.key, block.modules))
        )
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
                nice_run(["terraform", "state", "list"], check=True, capture_output=True)
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

        gen_tf.gen(ret, TF_FILE_PATH)
        if no_apply:
            continue
        print(f"Will now generate terraform plan for block {block_idx}.")
        amplitude_client.send_event(
            amplitude_client.PLAN_EVENT, event_properties={"block_idx": block_idx}
        )

        target_modules = list(current_module_keys)
        # On the last block run, destroy all modules that are in the remote state,
        # but have not been touched by any block.
        # Modules are untouched if the customer deletes or renames them in the
        # opta config file.
        # TODO: Warn user when things are getting deleted (when we have opta diffs)
        if block_idx + 1 == len(blocks_to_process):
            untouched_modules = list(total_modules_applied - current_module_keys)
            target_modules += untouched_modules

        targets = list(map(lambda x: f"-target=module.{x}", target_modules))

        # Always fetch the latest modules while we're still in active development.
        nice_run(["terraform", "get", "--update"], check=True)

        nice_run(["terraform", "init"], check=True)

        # When the test flag is passed, verify that terraform plan runs without issues,
        # but don't lock the state.
        if test:
            nice_run(["terraform", "plan", "-lock=false"] + targets, check=True)
            print("Plan ran successfully, skipping apply..")
            continue
        else:
            nice_run(
                [
                    "terraform",
                    "plan",
                    f"-out={TERRAFORM_PLAN_FILE_PATH}",
                    "-lock-timeout=60s",
                ]
                + targets,
                check=True,
            )

        click.confirm(
            "Terraform plan generation successful, would you like to apply?", abort=True
        )
        amplitude_client.send_event(
            amplitude_client.APPLY_EVENT, event_properties={"block_idx": block_idx}
        )
        nice_run(
            ["terraform", "apply", "-lock-timeout=60s"]
            + targets
            + [TERRAFORM_PLAN_FILE_PATH],
            check=True,
        )
        block_idx += 1


def _cleanup() -> None:
    try:
        os.remove(TF_FILE_PATH)
        os.remove(TERRAFORM_PLAN_FILE_PATH)
        os.remove(TF_STATE_FILE)
        os.remove(TF_STATE_BACKUP_FILE)
    except FileNotFoundError:
        pass


# Add commands
cli.add_command(secret)
cli.add_command(version)
cli.add_command(push)
cli.add_command(output)

if __name__ == "__main__":
    try:
        cli()
    except CalledProcessError as e:
        logger.exception(e)
        if e.stderr is not None:
            logger.error(e.stderr.decode("utf-8"))
        sys.exit(1)
    finally:
        if os.environ.get("OPTA_DEBUG") is None:
            _cleanup()
