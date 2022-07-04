from typing import Dict, Optional

import click
from kubernetes.client import CoreV1Api

import opta.constants as constants
from opta.amplitude import amplitude_client
from opta.commands.apply import local_setup
from opta.constants import SHELLS_ALLOWED
from opta.core.generator import gen_all
from opta.core.kubernetes import load_opta_kube_config, set_kube_config
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command()
@click.option(
    "-t",
    "--type",
    default=SHELLS_ALLOWED[0],
    help=f"Shell to use, one of {SHELLS_ALLOWED}, ",
    show_default=True,
    type=click.Choice(SHELLS_ALLOWED),
)
@config_option
@env_option
@input_variable_option
@local_option
def shell(
    env: Optional[str], config: str, type: str, local: Optional[bool], var: Dict[str, str]
) -> None:
    """
    Get a shell into one of the pods in a service

    Examples:

    opta shell -c my-service.yaml

    """

    config = check_opta_file_exists(config)
    if local:
        config = local_setup(config, input_variables=var)
    # Configure kubectl
    layer = Layer.load_from_yaml(
        config, env, input_variables=var, strict_input_variables=False
    )
    amplitude_client.send_event(
        amplitude_client.SHELL_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)
    set_kube_config(layer)
    load_opta_kube_config()
    context_name = layer.get_cloud_client().get_kube_context_name()

    # Get a random pod in the service
    v1 = CoreV1Api()
    pod_list = v1.list_namespaced_pod(layer.name).items
    if len(pod_list) == 0:
        raise UserErrors("This service is not yet deployed")

    nice_run(
        [
            "kubectl",
            "exec",
            "-n",
            layer.name,
            "-c",
            "k8s-service",
            "--kubeconfig",
            constants.GENERATED_KUBE_CONFIG or constants.DEFAULT_KUBECONFIG,
            "--context",
            context_name,
            pod_list[0].metadata.name,
            "-it",
            "--",
            type,
            "-il",
        ]
    )
