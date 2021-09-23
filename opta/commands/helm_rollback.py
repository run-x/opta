from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.core.kubernetes import configure_kubectl
from opta.helm import Helm
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@click.option("-h", "--helm-release", default=None, help="The release to roll back.")
def helm_rollback(config: str, env: Optional[str], helm_release: str) -> None:
    """
    Rolls back the Helm Releases.
    If nothing is provided in the helm release, it rolls back the pending-upgrade releases
    """
    check_opta_file_exists(config)
    amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    configure_kubectl(layer)

    if helm_release:
        release_list = Helm.get_helm_list(release=helm_release)
    else:
        release_list = Helm.get_helm_list(status="pending-upgrade")

    for release in release_list:
        Helm.rollback_helm(
            release["name"], namespace=release["namespace"], revision=release["revision"]
        )
