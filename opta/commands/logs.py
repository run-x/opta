from typing import Optional

import click
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl, tail_module_log
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
@click.option(
    "-s",
    "--seconds",
    default=None,
    help="Start showing logs from these many seconds in the past",
    show_default=False,
    type=int,
)
def logs(env: Optional[str], config: str, seconds: Optional[int]) -> None:
    """Get stream of logs from your service"""

    config = check_opta_file_exists(config)
    # Configure kubectl
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.SHELL_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)
    configure_kubectl(layer)
    load_kube_config()
    if layer.cloud == "aws":
        modules = layer.get_module_by_type("k8s-service")
    elif layer.cloud == "google":
        modules = layer.get_module_by_type("gcp-k8s-service")
    else:
        raise Exception(f"Currently not handling logs for cloud {layer.cloud}")
    if len(modules) == 0:
        raise UserErrors("No module of type (gcp-)k8s-service in the yaml file")
    elif len(modules) > 1:
        raise UserErrors(
            "Don't put more than one (gcp-)k8s-service module file per opta file"
        )
    module_name = modules[0].name
    tail_module_log(layer, module_name, seconds)
