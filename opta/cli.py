import sys
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.atexit import AtexitIntegration

from opta.constants import VERSION
from opta.core import terraform
from opta.core.generator import gen
from opta.exceptions import UserErrors
from opta.helpers.cli.push import get_ecr_auth_info, get_registry_url, push_to_docker
from opta.utils import is_tool, logger  # noqa: E402


def at_exit_callback(pending: int, timeout: float) -> None:
    """Don't be loud about sentry, our customer doesn't care about it."""

    def echo(msg):
        # type: (str) -> None
        sys.stderr.write(msg + "\n")

    if pending > 0:
        echo("Sentry is attempting to send %i pending error messages" % pending)
        echo("Waiting up to %s seconds" % timeout)
        echo("Press Ctrl-%s to quit" % (os.name == "nt" and "Break" or "C"))
    sys.stderr.flush()


def before_send(event: Any, hint: Any) -> Any:
    """Don't send us events caused by user errors"""
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, UserErrors):
            return None
    return event


if hasattr(sys, "_called_from_test") or VERSION == "dev":
    logger.debug("Not sending sentry cause we're in test or dev")
else:
    sentry_sdk.init(
        "https://aab05facf13049368d749e1b30a08b32@o511457.ingest.sentry.io/5610510",
        traces_sample_rate=1.0,
        integrations=[AtexitIntegration(at_exit_callback)],
        before_send=before_send,
    )


import json  # noqa: E402
import os  # noqa: E402
import os.path  # noqa: E402
from importlib.util import find_spec  # noqa: E402
from subprocess import CalledProcessError  # noqa: E402
from typing import List, Optional  # noqa: E402

import click  # noqa: E402

from opta.amplitude import amplitude_client  # noqa: E402
from opta.constants import TF_FILE_PATH  # noqa: E402
from opta.inspect_cmd import InspectCommand  # noqa: E402
from opta.kubectl import setup_kubectl  # noqa: E402
from opta.layer import Layer  # noqa: E402
from opta.nice_subprocess import nice_run  # noqa: E402
from opta.output import get_terraform_outputs  # noqa: E402
from opta.plugins.secret_manager import secret  # noqa: E402
from opta.version import version  # noqa: E402

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


@cli.command(hidden=True)
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--include-parent",
    is_flag=True,
    default=False,
    help="Also fetch outputs from the env (parent) layer",
)
@click.option(
    "--force-init",
    is_flag=True,
    default=False,
    help="Force regenerate opta setup files, instead of using cache",
)
@click.pass_context
def output(
    ctx: Any, configfile: str, env: Optional[str], include_parent: bool, force_init: bool,
) -> None:
    """ Print TF outputs """
    ctx.invoke(apply, configfile=configfile, env=env, no_apply=True)
    outputs = get_terraform_outputs(force_init, include_parent)
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)


@cli.command()
@click.argument("image")
@click.option("--configfile", default="opta.yml", help="Opta config file.")
@click.option("--env", default=None, help="The env to use when loading the config file.")
@click.option(
    "--tag",
    default=None,
    help="The image tag associated with your docker container. Defaults to your local image tag.",
)
@click.pass_context
def push(
    ctx: Any, image: str, configfile: str, env: str, tag: Optional[str] = None,
) -> None:
    if not is_tool("docker"):
        raise Exception("Please install docker on your machine")

    ctx.invoke(apply, configfile=configfile, env=env, no_apply=True)
    registry_url = get_registry_url()
    username, password = get_ecr_auth_info(configfile, env)
    push_to_docker(username, password, image, registry_url, tag)


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

    print("Found existing state")
    if not os.path.isdir("./.terraform") and not os.path.isfile("./terraform.tfstate"):
        if terraform.download_state(configfile, env):
            print("Found existing state")
        else:
            print("No existing state found. Assuming new build")

    layer = Layer.load_from_yaml(configfile, env)
    blocks_to_process = (
        layer.blocks[: max_block + 1] if max_block is not None else layer.blocks
    )

    for i in range(len(blocks_to_process)):
        gen(configfile, env, var, i)

        if no_apply:
            continue
        logger.debug(f"Will now initialize generate terraform plan for block {i}.")
        amplitude_client.send_event(
            amplitude_client.PLAN_EVENT, event_properties={"block_idx": i}
        )

        nice_run(["terraform", "init"], check=True)

        nice_run(
            [
                "terraform",
                "plan",
                f"-out={TERRAFORM_PLAN_FILE_PATH}",
                "-lock-timeout=60s",
            ],
            check=True,
        )

        click.confirm(
            "Terraform plan generation successful, would you like to apply?", abort=True
        )
        amplitude_client.send_event(
            amplitude_client.APPLY_EVENT, event_properties={"block_idx": i}
        )
        nice_run(
            ["terraform", "apply", "-lock-timeout=60s"] + [TERRAFORM_PLAN_FILE_PATH],
            check=True,
        )


def _cleanup() -> None:
    try:
        os.remove(TF_FILE_PATH)
        os.remove(TERRAFORM_PLAN_FILE_PATH)
        os.remove(TF_STATE_FILE)
        os.remove(TF_STATE_BACKUP_FILE)
    except FileNotFoundError:
        pass


# Initialize secret manager
cli.add_command(secret)

# Version command
cli.add_command(version)

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
