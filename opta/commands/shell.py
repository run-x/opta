from typing import Optional

import click
from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import check_opta_file_exists


@click.command()
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
def shell(env: Optional[str], config: str) -> None:
    """Get a bash shell into one of the pods in your service"""

    check_opta_file_exists(config)
    # Configure kubectl
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    amplitude_client.send_event(amplitude_client.SHELL_EVENT)
    gen_all(layer)
    configure_kubectl(layer)
    load_kube_config()

    # Get a random pod in the service
    v1 = CoreV1Api()
    pod_list = v1.list_namespaced_pod(layer.name).items
    if len(pod_list) == 0:
        raise UserErrors("This service is not yet deployed")

    nice_run(
        [
            "kubectl",
            "exec",
            "-n",
            layer.name,
            "-c",
            "k8s-service",
            pod_list[0].metadata.name,
            "-it",
            "--",
            "bash",
            "-il",
        ]
    )
