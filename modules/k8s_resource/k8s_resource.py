from typing import TYPE_CHECKING, Tuple

from modules.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

import yaml

from opta.core.kubernetes import GENERATED_KUBE_CONFIG_DIR


class K8sresourceProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-resource":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s-resource"
            )
        (
            module.data["kubeconfig"],
            module.data["kubecontext"],
        ) = self.get_k8s_config_context(layer)
        super(K8sresourceProcessor, self).__init__(module, layer)

    def get_k8s_config_context(self, layer: "Layer") -> Tuple[str, str]:
        if layer.cloud == "local":
            return "~/.kube/config", "kind-opta-local-cluster"
        else:
            config_file_name = f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{layer.root().name}-{layer.cloud}.yaml"
        with open(config_file_name, "r") as stream:
            context = (yaml.safe_load(stream))["current-context"]
        return config_file_name, context
