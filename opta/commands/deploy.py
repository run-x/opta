import re
from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _apply
from opta.commands.push import _push, get_push_tag, is_service_config
from opta.core.terraform import fetch_terraform_state_resources
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import fmt_msg, logger


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
    if not is_service_config(config):
        raise UserErrors(
            fmt_msg(
                """
            Opta deploy can only run on service yaml files. This is an environment yaml file.
            ~See https://docs.runx.dev/docs/reference/service_modules/ for more details.
            ~
            ~(We know that this is an environment yaml file, because service yaml must
            ~specify the "environments" field).
            """
            )
        )

    amplitude_client.send_event(amplitude_client.DEPLOY_EVENT)
    layer = Layer.load_from_yaml(config, env)

    print("hello there")
    try:
        state = fetch_terraform_state_resources(layer)
    except UserErrors as e:
        if (
            str(e)
            != "Could not fetch remote terraform state, assuming no resources exist yet."
        ):
            raise
        state = {}

    ecr_repo_pattern = re.compile(r"^module\..+\.aws_ecr_repository\.repo")
    ecr_repo = list(filter(ecr_repo_pattern.match, state.keys()))
    print("this happen", ecr_repo)
    if len(ecr_repo) == 0:
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
