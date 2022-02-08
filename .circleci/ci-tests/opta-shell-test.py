import os
import sys

from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config
from kubernetes.stream import stream

from opta.utils import yaml

configuration_file = sys.argv[1]

with open(configuration_file) as f:
    configuration = yaml.load(f.read())
    namespace = configuration["name"]

KUBECONFIG_PATH = os.environ.get("KUBECONFIG", "~/.kube/config")
load_kube_config(config_file=KUBECONFIG_PATH)

v1 = CoreV1Api()
pod_list = v1.list_namespaced_pod(namespace).items

response = stream(
    v1.connect_post_namespaced_pod_exec,
    pod_list[0].metadata.name,
    namespace,
    container="k8s-service",
    command=["/bin/bash", "-c", "echo test"],
    stderr=True,
    stdin=False,
    stdout=True,
    tty=False,
)

assert response.strip() == "test"
