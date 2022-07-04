from typing import Dict, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import local_setup
from opta.core.generator import gen_all
from opta.core.kubernetes import load_opta_kube_config, set_kube_config, tail_module_log
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command()
@click.option(
    "-s",
    "--seconds",
    default=None,
    help="Start showing logs from these many seconds in the past",
    show_default=False,
    type=int,
)
@config_option
@env_option
@input_variable_option
@local_option
def logs(
    env: Optional[str],
    config: str,
    seconds: Optional[int],
    local: Optional[bool],
    var: Dict[str, str],
) -> None:
    """
    Get stream of logs for a service

    Examples:

    opta logs -c my-service.yaml

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
    if layer.cloud == "aws":
        modules = layer.get_module_by_type("k8s-service")
    elif layer.cloud == "google":
        modules = layer.get_module_by_type("gcp-k8s-service")
    elif layer.cloud == "local":
        modules = layer.get_module_by_type("local-k8s-service")
    elif layer.cloud == "helm":
        modules = layer.get_module_by_type("local-k8s-service")
    else:
        raise Exception(f"Currently not handling logs for cloud {layer.cloud}")
    if len(modules) == 0:
        raise UserErrors("No module of type k8s-service in the yaml file")
    elif len(modules) > 1:
        raise UserErrors("Don't put more than one k8s-service module file per opta file")
    module_name = modules[0].name
    tail_module_log(layer, module_name, seconds)
