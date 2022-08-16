#!/usr/bin/env python3

import os.path
import sys

import click
from click_didyoumean import DYMGroup
from colored import attr, fg

from opta.cleanup_files import cleanup_files
from opta.commands.apply import apply
from opta.commands.deploy import deploy
from opta.commands.destroy import destroy
from opta.commands.events import events
from opta.commands.force_unlock import force_unlock
from opta.commands.generate_terraform import generate_terraform
from opta.commands.help import help
from opta.commands.inspect_cmd import inspect
from opta.commands.kubectl import configure_kubectl
from opta.commands.logs import logs
from opta.commands.output import output
from opta.commands.push import push
from opta.commands.secret import secret
from opta.commands.shell import shell
from opta.commands.show import show
from opta.commands.validate import validate
from opta.commands.version import version
from opta.crash_reporter import CURRENT_CRASH_REPORTER
from opta.exceptions import UserErrors
from opta.one_time import one_time
from opta.utils import logger


@click.group(cls=DYMGroup, context_settings=dict(help_option_names=["-h", "--help"]))
def cli() -> None:
    """Welcome to opta, runx's cli! Supercharge DevOps on any cloud

    Github: https://github.com/run-x/opta

    Documentation: https://docs.opta.dev/
    """
    pass


# Add commands
cli.add_command(apply)
cli.add_command(deploy)
cli.add_command(destroy)
cli.add_command(configure_kubectl)
cli.add_command(inspect)
cli.add_command(logs)
cli.add_command(output)
cli.add_command(push)
cli.add_command(secret)
cli.add_command(shell)
cli.add_command(validate)
cli.add_command(version)
cli.add_command(events)
cli.add_command(force_unlock)
cli.add_command(generate_terraform)
cli.add_command(help)
cli.add_command(show)


if __name__ == "__main__":
    try:
        # In case OPTA_DEBUG is set, local state files may not be cleaned up
        # after the command.
        # However, we should still clean them up before the next command, or
        # else it may interfere with it.
        one_time()
        cleanup_files()
        cli()
    except UserErrors as e:
        if os.environ.get("OPTA_DEBUG") is None:
            logger.error(str(e))
        else:
            logger.exception(str(e))
        logger.info(
            f"{fg('magenta')}If you need more help please reach out to the contributors in our slack channel at: https://slack.opta.dev{attr(0)}"
        )
        sys.exit(1)
    except Exception as e:
        logger.exception(str(e))
        logger.info(
            f"{fg('red')}Unhandled error encountered -- a crash report zipfile has been created for you. "
            "If you need more help please reach out (passing the crash report) to the contributors in our "
            f"slack channel at: https://slack.opta.dev{attr(0)}"
            "\nHint: As a first step in debugging, try rerunning the command and seeing if it still fails."
        )
        CURRENT_CRASH_REPORTER.generate_report()
        sys.exit(1)
    finally:
        # NOTE: Statements after the cli() invocation in the try clause are not executed.
        # A quick glance at click documentation did not show why that is the case or any workarounds.
        # Therefore adding this version check in the finally clause for now.
        if os.environ.get("OPTA_DEBUG") is None:
            cleanup_files()
