import subprocess
from typing import Optional

import click
from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl
from opta.exceptions import UserErrors
from opta.layer import Layer


@click.command()
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
def shell(env: Optional[str], config: str) -> None:
    """View a given secret of a k8s service"""
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.SHELL_EVENT)
    gen_all(layer)
    configure_kubectl(layer)
    load_kube_config()
    v1 = CoreV1Api()
    pod_list = v1.list_namespaced_pod(layer.name).items
    if len(pod_list) == 0:
        raise UserErrors("This service is not yet deployed")
    subprocess.Popen(
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
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
