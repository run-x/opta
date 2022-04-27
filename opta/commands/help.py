# type: ignore
from typing import Optional

import click
from click import Context
from click_didyoumean import DYMGroup

from opta.exceptions import UserErrors


@click.command()
@click.pass_context
@click.argument("command", required=False)
def help(context: Context, command: Optional[str]) -> None:
    """
    Get help for Opta.

    Example:

    opta help

    opta help apply
    """
    command_context: DYMGroup = context.parent.command
    if command is not None:
        try:
            command_context = command_context.commands[command]
        except KeyError:
            raise UserErrors(
                "Invalid Command. Please use correct commands mentioned in `opta help|-h|--help "
            )
    print(command_context.get_help(context))
