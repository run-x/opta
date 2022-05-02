import webbrowser

import click

UI_URL = "https://app.runx.dev/yaml-generator"


@click.command(hidden=True)
def ui() -> None:
    """
    Open the interactive UI
    """
    print(
        f"""
You will now be redirected to Opta's Yaml Generation UI.
If the browser doesn't open, please follow the link: {UI_URL}
        """
    )
    webbrowser.open(UI_URL)
