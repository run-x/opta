from typing import Dict, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import local_setup
from opta.core.kubernetes import load_opta_kube_config_to_default, purge_opta_kube_config
from opta.core.kubernetes import set_kube_config as configure
from opta.layer import Layer
from opta.opta_lock import opta_acquire_lock, opta_release_lock
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command()
@config_option
@env_option
@input_variable_option
@local_option
def configure_kubectl(
    config: str, env: Optional[str], local: Optional[bool], var: Dict[str, str]
) -> None:
    """
    Configure kubectl so you can connect to the cluster

    This command constructs a configuration with prepopulated server and certificate authority data values for the managed cluster.

    If you have the KUBECONFIG environment variable set, then the resulting configuration file is created at that location.
    Otherwise, by default, the resulting configuration file is created at the default kubeconfig path (.kube/config) in your home directory.
    """
    try:
        opta_acquire_lock()
        config = check_opta_file_exists(config)
        if local:
            config = local_setup(config, input_variables=var)
        layer = Layer.load_from_yaml(
            config, env, input_variables=var, strict_input_variables=False
        )
        amplitude_client.send_event(
            amplitude_client.CONFIGURE_KUBECTL_EVENT,
            event_properties={"org_name": layer.org_name, "layer_name": layer.name},
        )
        layer.verify_cloud_credentials()
        purge_opta_kube_config(layer)
        configure(layer)
        load_opta_kube_config_to_default(layer)
    finally:
        opta_release_lock()
