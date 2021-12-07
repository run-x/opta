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
    """Force Unlocks a stuck lock on the current workspace

    Examples:

    opta force-unlock -c my_config.yaml -e prod.yaml
    """
    tf_flags: List[str] = []
    config = check_opta_file_exists(config)
    amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    modules = Terraform.get_existing_modules(layer)
    layer.modules = [x for x in layer.modules if x.name in modules]
    gen_all(layer)

    if Terraform.download_state(layer):
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

        if "k8scluster" in modules:
            configure_kubectl(layer)
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

    # Terraform.init(layer=layer)
    #
    # click.confirm(
    #     "This will remove the lock on the remote state."
    #     "\nPlease make sure that no other instance of opta command is running on this file."
    #     "\nDo you still want to proceed?",
    #     abort=True,
    # )
    #
    # Terraform.force_unlock(layer, *tf_flags)
    #
    # click.confirm(
    #     "Do you also wish to Rollback the Helm releases in Pending-Upgrade State?"
    #     "\nPlease make sure that no other instance of opta command is running on this file."
    #     "\nDo you still want to proceed?",
    #     abort=True,
    # )
    # configure_kubectl(layer)
    #
    # release_list = Helm.get_helm_list(status="pending-upgrade")
    #
    # for release in release_list:
    #     Helm.rollback_helm(
    #         release["name"], namespace=release["namespace"], revision=release["revision"]
    #     )


# def _check_cluster_exists(layer: "Layer") -> bool:
#     if layer.get_module_by_type()
