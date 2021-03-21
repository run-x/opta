from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _apply
from opta.commands.push import _push, get_push_tag
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import logger


@click.command()
@click.option(
    "-i", "--image", required=True, help="Your local image in the for myimage:tag"
)
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
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    help="Automatically approve terraform plan.",
)
def deploy(
    image: str, config: str, env: Optional[str], tag: Optional[str], auto_approve: bool
) -> None:
    """Push your new image to the cloud and deploy it in your environment"""
    amplitude_client.send_event(amplitude_client.DEPLOY_EVENT)
    layer = Layer.load_from_yaml(config, env)
    try:
        outputs = Terraform.get_outputs(layer)
    except UserErrors as e:
        if (
            str(e)
            != "Could not fetch remote terraform state, assuming no resources exist yet."
        ):
            raise
        outputs = {}
    if "docker_repo_url" not in outputs:
        logger.info(
            "Did not find docker repository in state, so applying once to create it before deployment"
        )
        _apply(
            config=config,
            env=env,
            refresh=False,
            max_module=None,
            image_tag=None,
            test=False,
            auto_approve=auto_approve,
        )
    _push(image=image, config=config, env=env, tag=tag)
    image_tag = get_push_tag(image, tag)
    _apply(
        config=config,
        env=env,
        refresh=False,
        max_module=None,
        image_tag=image_tag,
        test=False,
        auto_approve=auto_approve,
    )
