from typing import List, Optional

import click

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import check_opta_file_exists


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@click.option(
    "-f",
    "--force-terraform",
    is_flag=True,
    default=False,
    help="Automatically approve terraform plan.",
)
def force_unlock(config: str, env: Optional[str], force_terraform: bool) -> None:
    """Force Unlocks a stuck lock on the current workspace"""
    check_opta_file_exists(config)
    amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    gen_all(layer)

    Terraform.init()

    tf_flags: List[str] = []

    if not force_terraform:
        click.confirm(
            "Do you really want to force-unlock?"
            "\t\nTerraform will remove the lock on the remote state."
            "\t\nThis will allow local Terraform commands to modify this state, even though it may be still be in use.",
            abort=True,
        )
    else:
        tf_flags.append("-force")

    Terraform.force_unlock(layer, *tf_flags)
