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
    if command is not None and not context.parent.command.commands.__contains__(command):
        raise UserErrors("Invalid Command")
    if command:
        command_context = context.parent.command.commands.get(command)
    print(command_context.get_help(context))
