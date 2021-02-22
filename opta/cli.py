import os
import os.path
import sys
from importlib.util import find_spec
from subprocess import CalledProcessError
from typing import Optional, Set

import click

import opta.sentry  # noqa: F401 This leads to initialization of sentry sdk
from opta.amplitude import amplitude_client
from opta.commands.inspect_cmd import inspect
from opta.commands.kubectl import configure_kubectl
from opta.commands.output import output
from opta.commands.push import push
from opta.commands.secret import secret
from opta.commands.version import version
from opta.constants import TF_FILE_PATH
from opta.core.generator import gen
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import is_tool, logger

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
@click.option("--config", default="opta.yml", help="Opta config file", show_default=True)
@click.option(
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Run from first block, regardless of current state",
    hidden=True,
)
@click.option(
    "--max-module", default=None, type=int, help="Max module to process", hidden=True
)
@click.option(
    "--image-tag",
    default=None,
    type=str,
    help="If this handles a service, it's the image tag you wanna deploy",
    hidden=True,
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run tf plan, but don't lock state file",
    hidden=True,
)
def apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: str,
    test: bool,
) -> None:
    """Apply your opta config file to your infrastructure!"""
    _apply(config, env, refresh, max_module, image_tag, test)


def _apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: str,
    test: bool,
) -> None:
    """ Generate TF file based on opta config file """
    if not is_tool("terraform"):
        raise UserErrors("Please install terraform on your machine")
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.variables["image_tag"] = image_tag
    Terraform.create_storage(layer)

    existing_modules: Set[str] = set()
    for module_idx, current_modules, total_block_count in gen(layer):
        if module_idx == 0:
            # This is set during the first iteration, since the tf file must exist.
            existing_modules = Terraform.get_existing_modules(layer)
        configured_modules = set([x.name for x in current_modules])
        is_last_module = module_idx == total_block_count - 1
        has_new_modules = not configured_modules.issubset(existing_modules)
        if not is_last_module and not has_new_modules and not refresh:
            continue
        if is_last_module:
            untouched_modules = list(existing_modules - configured_modules)
            current_modules += untouched_modules

        targets = list(map(lambda x: f"-target=module.{x}", configured_modules))

        if test:
            Terraform.plan("-lock=false", *targets)
            print("Plan ran successfully, not applying since this is a test.")
        else:
            amplitude_client.send_event(
                amplitude_client.APPLY_EVENT, event_properties={"module_idx": module_idx}
            )
            Terraform.apply("-lock-timeout=60s", *targets)


def _cleanup() -> None:
    try:
        os.remove(TF_FILE_PATH)
        os.remove(TF_STATE_FILE)
        os.remove(TF_STATE_BACKUP_FILE)
    except FileNotFoundError:
        pass


# Add commands
cli.add_command(configure_kubectl)
cli.add_command(inspect)
cli.add_command(output)
cli.add_command(push)
cli.add_command(secret)
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
