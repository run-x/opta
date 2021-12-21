from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl as configure
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option(
    "-c", "--config", default="opta.yaml", help="Opta config file", show_default=True
)
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
def configure_kubectl(config: str, env: Optional[str]) -> None:
    """Configure the kubectl CLI tool for the given cluster"""

    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.CONFIGURE_KUBECTL_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)

    configure(layer)
