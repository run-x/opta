import webbrowser

import click


@click.command()
def init() -> None:
    """
    This command brings to you an interactive way of creating an opta configuration file.
    You can choose to create an environment configuration or a service file by using the command.

    You will now be redirected to Opta's Yaml Generation UI. If the browser doesn't open, please open the Link.

    `https://app.runx.dev/yaml-generator`
    """
    webbrowser.open("https://app.runx.dev/yaml-generator")
