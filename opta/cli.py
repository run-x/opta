import os
import os.path
import sys
from importlib.util import find_spec
from subprocess import CalledProcessError
from typing import Any, List, Optional

import click

import opta.sentry  # noqa: F401 This leads to initialization of sentry sdk
from opta.amplitude import amplitude_client  # noqa: E402
from opta.commands.output import output  # noqa: E402
from opta.commands.push import push  # noqa: E402
from opta.commands.secret import secret  # noqa: E402
from opta.commands.version import version  # noqa: E402
from opta.constants import TF_FILE_PATH  # noqa: E402
from opta.core import terraform  # noqa: E402
from opta.core.generator import gen  # noqa: E402
from opta.exceptions import UserErrors  # noqa: E402
from opta.inspect_cmd import InspectCommand  # noqa: E402
from opta.kubectl import setup_kubectl  # noqa: E402
from opta.nice_subprocess import nice_run  # noqa: E402
from opta.utils import initialize_logger, is_tool, logger  # noqa: E402

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
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)

    existing_state = True
    if terraform.download_state(configfile, env):
        logger.info("Found existing state")
    else:
        existing_state = False
        logger.info("No existing state found. Assuming new build")

    for (cur, total) in gen(configfile, env, var):
        if no_apply:
            continue

        if existing_state and cur != total - 1:
            # If existing_state then we just run apply after the last block
            # TODO: Deleting blocks after the first run will lead to undefined behavior!
            # Note that deleting resources in the last block will still work as expected
            continue

        logger.debug(f"Will now initialize generate terraform plan for block {cur}.")
        nice_run(["terraform", "init"], check=True)

        amplitude_client.send_event(
            amplitude_client.APPLY_EVENT, event_properties={"block_idx": cur}
        )
        # We don't set check=True here because terraform apply exits with 1 if
        # user says no to the apply
        nice_run(["terraform", "apply", "-lock-timeout=60s"])


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
    initialize_logger()
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
