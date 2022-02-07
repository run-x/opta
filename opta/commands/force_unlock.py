from typing import List, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import _local_setup
from opta.core.generator import gen_all
from opta.core.helm import Helm
from opta.core.kubernetes import set_kube_config
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import local_option


@click.command()
@click.option("-c", "--config", default="opta.yaml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@local_option
def force_unlock(config: str, env: Optional[str], local: Optional[bool]) -> None:
    """Release a stuck lock on the current workspace

    Manually unlock the state for the defined configuration.

    This will not modify your infrastructure. This command removes the lock on the
    state for the current workspace.

    Examples:

    opta force-unlock -c my-config.yaml -e prod
    """
    tf_flags: List[str] = []
    config = check_opta_file_exists(config)
    if local:
        config = _local_setup(config)
    amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    modules = Terraform.get_existing_modules(layer)
    layer.modules = [x for x in layer.modules if x.name in modules]
    gen_all(layer)

    tf_lock_exists, _ = Terraform.tf_lock_details(layer)
    if tf_lock_exists:
        Terraform.init(layer=layer)
        click.confirm(
            "This will remove the lock on the remote state."
            "\nPlease make sure that no other instance of opta command is running on this file."
            "\nDo you still want to proceed?",
            abort=True,
        )
        tf_flags.append("-force")
        Terraform.force_unlock(layer, *tf_flags)

    if Terraform.download_state(layer):
        if layer.parent is not None or "k8scluster" in modules:
            set_kube_config(layer)
            pending_upgrade_release_list = Helm.get_helm_list(status="pending-upgrade")
            click.confirm(
                "Do you also wish to Rollback the Helm releases in Pending-Upgrade State?"
                "\nPlease make sure that no other instance of opta command is running on this file."
                "\nDo you still want to proceed?",
                abort=True,
            )

            for release in pending_upgrade_release_list:
                Helm.rollback_helm(
                    release["name"],
                    namespace=release["namespace"],
                    revision=release["revision"],
                )
