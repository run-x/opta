from typing import TYPE_CHECKING, Tuple

from modules.base import ModuleProcessor
from opta.core.kubernetes import set_kube_config

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

import os

import yaml


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

    def process(self, module_idx: int) -> None:
        file_path: str = self.module.data.get("file_path")
        if not file_path.startswith("/"):
            file_path = os.path.join(os.path.dirname(self.layer.path), file_path)
        self.module.data["file_path"] = file_path
        super(K8smanifestProcessor, self).process(module_idx)

    def get_k8s_config_context(self, layer: "Layer") -> Tuple[str, str]:
        set_kube_config(layer)
        if layer.cloud == "local":
            return "~/.kube/config", "kind-opta-local-cluster"
        else:
            config_file_name = layer.get_kube_config_file_name()
        with open(config_file_name, "r") as stream:
            context = (yaml.safe_load(stream))["current-context"]
        return config_file_name, context
