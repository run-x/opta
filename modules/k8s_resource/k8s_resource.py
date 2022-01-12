from typing import TYPE_CHECKING
from kubernetes.config import load_kube_config

from modules.base import ModuleProcessor
from opta.core.kubernetes import configure_kubectl

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module
from opta.core.kubernetes import GENERATED_KUBE_CONFIG_DIR
import yaml
from opta.nice_subprocess import nice_run
class K8sresourceProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-resource":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s-resource"
            )
        module.data["kubeconfig"], module.data["kubecontext"] = self.get_k8s_config_context(layer)
        super(K8sresourceProcessor, self).__init__(module, layer)

    def get_k8s_config_context(self, layer):
        if layer.cloud == "local":
            return "~/.kube/config", "kind-opta-local-cluster"
        else:
            config_file_name = (
        f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{layer.root().name}-{layer.cloud}.yaml"
    )
        with open(config_file_name, "r") as stream:
            context = (yaml.safe_load(stream))["current-context"]
        return config_file_name, context
    