import os
import sys

import yaml
from kubernetes.client import CoreV1Api
from kubernetes.config import load_kube_config
from kubernetes.stream import stream

configuration_file = sys.argv[1]

namespace = None
with open(configuration_file) as f:
    configuration = yaml.load(f, Loader=yaml.FullLoader)
    namespace = configuration["name"]

KUBECONFIG_PATH = os.environ.get("KUBECONFIG", "~/.kube/config")
load_kube_config(config_file=KUBECONFIG_PATH)

v1 = CoreV1Api()
pod_list = v1.list_namespaced_pod(namespace).items

test_value = "test"

response = stream(
    v1.connect_post_namespaced_pod_exec,
    pod_list[0].metadata.name,
    namespace,
    container="k8s-service",
    command=["/bin/bash", "-c", f"echo {test_value}"],
    stderr=True,
    stdin=False,
    stdout=True,
    tty=False,
)

assert response.strip() == test_value
