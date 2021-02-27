import subprocess
from typing import List, Optional

import click
from kubernetes.config import load_kube_config

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module


def get_k8s_service_module(modules: List[Module]) -> Module:
    for m in modules:
        if m.type == "k8s-service":
            return m
    raise UserErrors("No module of type k8s-service in the yaml file")


@click.command()
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
def logs(env: Optional[str], config: str) -> None:
    """View a given secret of a k8s service"""
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.SHELL_EVENT)
    gen_all(layer)
    configure_kubectl(layer)
    load_kube_config()
    module_name = get_k8s_service_module(layer.modules).name
    subprocess.Popen(
        [
            "kubectl",
            "logs",
            "-f",
            "-n",
            layer.name,
            "-c",
            "k8s-service",
            "-l",
            f"app.kubernetes.io/instance={layer.name}-{module_name}",
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
