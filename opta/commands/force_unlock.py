from typing import List, Optional

import click

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.helm import Helm
from opta.core.kubernetes import configure_kubectl
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
def force_unlock(config: str, env: Optional[str]) -> None:
    """Force Unlocks a stuck lock on the current workspace"""
    tf_flags: List[str] = []
    check_opta_file_exists(config)
    amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    gen_all(layer)

    Terraform.init(layer=layer)

    click.confirm(
        "This will remove the lock on the remote state."
        "\n\tPlease make sure that no other instance of opta command is running on this file."
        "\n\tDo you still want to proceed?",
        abort=True,
    )

    Terraform.force_unlock(layer, *tf_flags)
    configure_kubectl(layer)

    release_list = Helm.get_helm_list(status="pending-upgrade")

    for release in release_list:
        Helm.rollback_helm(
            release["name"], namespace=release["namespace"], revision=release["revision"]
        )
