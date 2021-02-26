from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _apply
from opta.commands.push import _push, get_push_tag


@click.command()
@click.option("-i", "--image", help="Your local image in the for myimage:tag")
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@click.option(
    "-t",
    "--tag",
    default=None,
    help="The image tag associated with your docker container. Defaults to your local image tag.",
)
def deploy(image: str, config: str, env: Optional[str], tag: Optional[str]) -> None:
    """Push your new image to the cloud and deploy it in your environment"""
    amplitude_client.send_event(amplitude_client.DEPLOY_EVENT)
    _push(image=image, config=config, env=env, tag=tag)
    image_tag = get_push_tag(image, tag)
    _apply(
        config=config,
        env=env,
        refresh=False,
        max_module=None,
        image_tag=image_tag,
        test=False,
    )
