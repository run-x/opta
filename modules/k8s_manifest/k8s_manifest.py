from typing import TYPE_CHECKING, Tuple

from modules.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

import yaml

from opta.core.kubernetes import get_kube_config_file_name


class K8smanifestProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-manifest":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s-manifest"
            )
        (
            module.data["kubeconfig"],
            module.data["kubecontext"],
        ) = self.get_k8s_config_context(layer)
        super(K8smanifestProcessor, self).__init__(module, layer)

    def get_k8s_config_context(self, layer: "Layer") -> Tuple[str, str]:
        if layer.cloud == "local":
            return "~/.kube/config", "kind-opta-local-cluster"
        else:
            config_file_name = get_kube_config_file_name(layer)
        with open(config_file_name, "r") as stream:
            context = (yaml.safe_load(stream))["current-context"]
        return config_file_name, context
