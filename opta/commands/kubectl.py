from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.core.kubernetes import load_opta_kube_config_to_default, purge_opta_kube_config
from opta.core.kubernetes import set_kube_config as configure
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Purge the existing cached kube config",
)
def configure_kubectl(config: str, env: Optional[str], force: bool) -> None:
    """
    Configure kubectl so you can connect to the cluster

    This command constructs a configuration with prepopulated server and certificate authority data values for the managed cluster.

    If you have the KUBECONFIG environment variable set, then the resulting configuration file is created at that location.
    Otherwise, by default, the resulting configuration file is created at the default kubeconfig path (.kube/config) in your home directory.
    """

    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.CONFIGURE_KUBECTL_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    if force:
        purge_opta_kube_config(layer)
    configure(layer)
    load_opta_kube_config_to_default(layer)
