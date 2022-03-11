from typing import Dict, List, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _apply, local_setup
from opta.commands.push import is_service_config, push_image
from opta.core.terraform import Terraform
from opta.error_constants import USER_ERROR_TF_LOCK
from opta.exceptions import MissingState, UserErrors
from opta.layer import Layer
from opta.module import Module
from opta.opta_lock import opta_acquire_lock, opta_release_lock
from opta.pre_check import pre_check
from opta.utils import check_opta_file_exists, fmt_msg, logger
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command()
@click.option(
    "-i", "--image", help="Your local image in the for myimage:tag", default=None
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
@config_option
@env_option
@input_variable_option
@local_option
def deploy(
    image: str,
    config: str,
    env: Optional[str],
    tag: Optional[str],
    auto_approve: bool,
    detailed_plan: bool,
    local: Optional[bool],
    var: Dict[str, str],
) -> None:
    """Deploys an image to Kubernetes

    - Pushes the local image to private container registry (ECR, GCR, ACR), if configuration contains `image: AUTO`,
      else uses the image provided from a Repo.

    - Update the kubernetes deployment to use the new image.

    - Create new pods to use the new image - automatically done by kubernetes.

    Examples:

    opta deploy -c image-auto-configuration.yaml -i image:local --auto-approve

    opta deploy -c repo-provided-configuration.yaml -e prod

    opta deploy -c my-service.yaml -i my-image:latest --local

    Documentation: https://docs.opta.dev/features/custom_image/

    """

    try:
        opta_acquire_lock()
        pre_check()

        config = check_opta_file_exists(config)
        if local:
            config = local_setup(
                config, image_tag=tag, refresh_local_env=True, input_variables=var
            )
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

        layer = Layer.load_from_yaml(config, env, input_variables=var)
        amplitude_client.send_event(
            amplitude_client.DEPLOY_EVENT,
            event_properties={"org_name": layer.org_name, "layer_name": layer.name},
        )
        is_auto = __check_layer_and_image(layer, image)
        layer.verify_cloud_credentials()
        layer.validate_required_path_dependencies()
        if Terraform.download_state(layer):
            tf_lock_exists, _ = Terraform.tf_lock_details(layer)
            if tf_lock_exists:
                raise UserErrors(USER_ERROR_TF_LOCK)

        try:
            outputs = Terraform.get_outputs(layer)
        except MissingState:
            outputs = {}

        image_digest, image_tag = (None, None)
        if is_auto:
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
                    input_variables=var,
                )
            if image is not None:
                image_digest, image_tag = push_image(
                    image=image, config=config, env=env, tag=tag, input_variables=var,
                )
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
            input_variables=var,
        )
    finally:
        opta_release_lock()


def __check_layer_and_image(layer: "Layer", option_image: str) -> bool:
    k8s_modules: List[Module] = layer.get_module_by_type("k8s-service")
    if len(k8s_modules) == 0:
        raise UserErrors("k8s-service module not present.")
    configuration_image_name: str = k8s_modules[0].data.get("image")  # type: ignore
    configuration_image_name = configuration_image_name.lower()
    if configuration_image_name != "auto" and option_image is not None:
        raise UserErrors(
            f"Do not pass any image. Image {configuration_image_name} already present in configuration."
        )
    return configuration_image_name == "auto"
