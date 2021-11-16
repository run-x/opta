import webbrowser

import click


@click.command()
def init() -> None:
    """
    Opens the interactive UI
    You can choose to create an environment configuration or a service file by using the command.
    """
    print(
        "You will now be redirected to Opta's Yaml Generation UI. If the browser doesn't open, please follow the link: "
        "`https://app.runx.dev/yaml-generator`"
    )
    webbrowser.open("https://app.runx.dev/yaml-generator")
