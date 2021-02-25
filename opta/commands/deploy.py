from typing import Optional

import click

from opta.commands.apply import apply
from opta.commands.push import get_push_tag, push


@click.command()
@click.argument("image")
@click.option("--config", default="opta.yml", help="Opta config file.")
@click.option("--env", default=None, help="The env to use when loading the config file.")
@click.option(
    "--tag",
    default=None,
    help="The image tag associated with your docker container. Defaults to your local image tag.",
)
def deploy(image: str, config: str, env: Optional[str], tag: Optional[str]) -> None:
    push(image=image, config=config, env=env, tag=tag)
    image_tag = get_push_tag(image, tag)
    apply(
        config=config,
        env=env,
        refresh=False,
        max_module=None,
        image_tag=image_tag,
        test=False,
    )
