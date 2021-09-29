from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists, logger


# Rollback automatically runs when terraform apply fails.
# This explicit command for rollback is primarily for debugging/development.
@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
def rollback(config: str, env: Optional[str]) -> None:
    """Destroy any stale opta resources in the current layer"""

    check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    if not Terraform.download_state(layer):
        logger.info(
            "The opta state could not be found. This may happen if destroy ran successfully before."
        )
        return
    tf_lock_exists, _ = Terraform.tf_lock_details(layer)
    if tf_lock_exists:
        raise UserErrors(
            "Terraform Lock exists on the given configuration."
            "\nEither wait for sometime for the Terraform to release lock."
            "\nOr use force-unlock command to release the lock."
        )
    gen_all(layer)
    Terraform.rollback(layer)
