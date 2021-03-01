import time
from threading import Thread
from typing import List, Optional, Set

import click
from colored import attr, fg
from kubernetes.client import ApiException, CoreV1Api, V1Pod
from kubernetes.config import load_kube_config
from kubernetes.watch import Watch

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.kubernetes import configure_kubectl
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module import Module
from opta.utils import logger


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
@click.option(
    "-s",
    "--seconds",
    default=None,
    help="Start showing logs from these many seconds in the past",
    show_default=False,
    type=int,
)
def logs(env: Optional[str], config: str, seconds: Optional[int]) -> None:
    """Get stream of logs from your service"""

    # Configure kubectl
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(amplitude_client.SHELL_EVENT)
    gen_all(layer)
    configure_kubectl(layer)
    load_kube_config()
    module_name = get_k8s_service_module(layer.modules).name
    log_main(layer, module_name, seconds)


def log_main(layer: Layer, module_name: str, seconds: Optional[int]) -> None:
    current_pods_monitored: Set[str] = set()
    v1 = CoreV1Api()
    watch = Watch()
    count = 0
    try:
        for event in watch.stream(
            v1.list_namespaced_pod,
            namespace=layer.name,
            label_selector=f"app.kubernetes.io/instance={layer.name}-{module_name}",
        ):
            pod: V1Pod = event["object"]
            color_idx = count % 256 + 1
            if pod.metadata.name not in current_pods_monitored:
                current_pods_monitored.add(pod.metadata.name)
                new_thread = Thread(
                    target=log_pod,
                    args=(layer.name, pod, color_idx, seconds),
                    daemon=True,
                )
                new_thread.start()
                count += 1
    finally:
        pass


def log_pod(namespace: str, pod: V1Pod, color_idx: int, seconds: Optional[int]) -> None:
    v1 = CoreV1Api()
    watch = Watch()
    print(
        f"{fg(color_idx)}Showing the logs for server {pod.metadata.name} of your service{attr(0)}"
    )
    retry_count = 0
    while True:
        try:
            for logline in watch.stream(
                v1.read_namespaced_pod_log,
                name=pod.metadata.name,
                namespace=namespace,
                container="k8s-service",
                since_seconds=seconds,
            ):
                print(f"{fg(color_idx)}{pod.metadata.name} {logline}{attr(0)}")
        except ApiException as e:
            if e.status == 404:
                print(
                    f"{fg(color_idx)}Server {pod.metadata.name} has been terminated{attr(0)}"
                )
                return
            elif retry_count < 5:
                print(
                    f"{fg(color_idx)}Couldn't get logs, waiting a bit and retrying{attr(0)}"
                )
                time.sleep(1 << retry_count)
                retry_count += 1
            else:
                logger.error(
                    f"Got the following error while trying to fetch the logs for pod {pod.metadata.name} in namespace {namespace}: {e}"
                )
                return
        except Exception as e:
            logger.error(
                f"Got the following error while trying to fetch the logs for pod {pod.metadata.name} in namespace {namespace}: {e}"
            )
            return
