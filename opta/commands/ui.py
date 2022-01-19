import webbrowser

import click

UI_URL = "https://app.runx.dev/yaml-generator"


@click.command()
def ui() -> None:
    """
    Opens the interactive UI
    """
    print(
        f"""
You will now be redirected to Opta's Yaml Generation UI.
If the browser doesn't open, please follow the link: {UI_URL}
        """
    )
    webbrowser.open(UI_URL)
