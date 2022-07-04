from typing import Dict, List, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import local_setup
from opta.core.generator import gen_all
from opta.core.helm import Helm
from opta.core.kubernetes import set_kube_config
from opta.core.terraform import Terraform
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
def force_unlock(
    config: str, env: Optional[str], local: Optional[bool], var: Dict[str, str],
) -> None:
    """Release a stuck lock on the current workspace

    Manually unlock the state for the defined configuration.

    This will not modify your infrastructure. This command removes the lock on the
    state for the current workspace.

    Examples:

    opta force-unlock -c my-config.yaml -e prod
    """
    try:
        opta_acquire_lock()
        tf_flags: List[str] = []
        config = check_opta_file_exists(config)
        if local:
            config = local_setup(config, input_variables=var)
        amplitude_client.send_event(amplitude_client.FORCE_UNLOCK_EVENT)
        layer = Layer.load_from_yaml(
            config, env, input_variables=var, strict_input_variables=False
        )
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
                kube_context = layer.get_cloud_client().get_kube_context_name()
                pending_upgrade_release_list = Helm.get_helm_list(
                    kube_context=kube_context, status="pending-upgrade"
                )
                click.confirm(
                    "Do you also wish to Rollback the Helm releases in Pending-Upgrade State?"
                    "\nPlease make sure that no other instance of opta command is running on this file."
                    "\nDo you still want to proceed?",
                    abort=True,
                )

                for release in pending_upgrade_release_list:
                    Helm.rollback_helm(
                        kube_context,
                        release["name"],
                        namespace=release["namespace"],
                        revision=release["revision"],
                    )
    finally:
        opta_release_lock()
