from typing import Optional

import click
from click import Context

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
    command_context = context.parent.command  # type: ignore
    if command is not None:
        try:
            command_context = command_context.commands[command]  # type: ignore
        except KeyError:
            raise UserErrors(
                "Invalid Command. Please use correct commands mentioned in `opta help|-h|--help "
            )
    print(command_context.get_help(context))
