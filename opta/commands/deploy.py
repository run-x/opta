from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _apply
from opta.commands.local_flag import _clean_tf_folder, _handle_local_flag
from opta.commands.push import _push, is_service_config
from opta.core.terraform import Terraform
from opta.error_constants import USER_ERROR_TF_LOCK
from opta.exceptions import MissingState, UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists, fmt_msg, logger


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
@click.option(
    "--detailed-plan",
    is_flag=True,
    default=False,
    help="Show full terraform plan in detail, not the opta provided summary",
)
@click.option(
    "--local",
    is_flag=True,
    default=False,
    help="""Run the service locally on a local Kubernetes cluster for development and testing,  irrespective of the environment specified inside the opta service yaml file""",
    hidden=False,
)
def deploy(
    image: str,
    config: str,
    env: Optional[str],
    tag: Optional[str],
    auto_approve: bool,
    detailed_plan: bool,
    local: Optional[bool],
) -> None:
    """Push your new image to the cloud and deploy it in your environment"""

    check_opta_file_exists(config)
    if not is_service_config(config):
        raise UserErrors(
            fmt_msg(
                """
            Opta deploy can only run on service yaml files. This is an environment yaml file.
            ~See https://docs.opta.dev/getting-started/ for more details.
            ~
            ~(We think that this is an environment yaml file, because service yaml must
            ~specify the "environments" field).
            """
            )
        )

    if local:
        adjusted_config = _handle_local_flag(config, False)
        if adjusted_config != config:  # Only do this for service opta files
            config = adjusted_config
            _apply(
                config="config/localopta.yml",
                auto_approve=True,
                local=False,
                env="",
                refresh=True,
                image_tag="",
                test=False,
                detailed_plan=True,
            )
            _clean_tf_folder()

    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.DEPLOY_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    if Terraform.download_state(layer):
        tf_lock_exists, _ = Terraform.tf_lock_details(layer)
        if tf_lock_exists:
            raise UserErrors(USER_ERROR_TF_LOCK)

    try:
        outputs = Terraform.get_outputs(layer)
    except MissingState:
        outputs = {}
    if "docker_repo_url" not in outputs or outputs["docker_repo_url"] == "":
        logger.info(
            "Did not find docker repository in state, so applying once to create it before deployment"
        )
        _apply(
            config=config,
            env=env,
            refresh=False,
            image_tag=None,
            test=False,
            local=local,
            auto_approve=auto_approve,
            stdout_logs=False,
            detailed_plan=detailed_plan,
        )
    image_digest, image_tag = _push(image=image, config=config, env=env, tag=tag)
    _apply(
        config=config,
        env=env,
        refresh=False,
        image_tag=None,
        test=False,
        local=local,
        auto_approve=auto_approve,
        image_digest=image_digest,
        detailed_plan=detailed_plan,
    )
