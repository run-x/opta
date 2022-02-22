from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.core.kubernetes import (
    add_linkerd_label_to_kubesystem,
    list_namespaces,
    set_kube_config,
)

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AzureK8sBaseProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "azure-k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(AzureK8sBaseProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        set_kube_config(self.layer)
        add_linkerd_label_to_kubesystem()
        list_namespaces()
        super(AzureK8sBaseProcessor, self).pre_hook(module_idx)

    def process(self, module_idx: int) -> None:
        byo_cert_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "external-ssl-cert":
                byo_cert_module = module
                break
        if byo_cert_module is not None:
            self.module.data[
                "private_key"
            ] = f"${{{{module.{byo_cert_module.name}.private_key}}}}"
            self.module.data[
                "certificate_body"
            ] = f"${{{{module.{byo_cert_module.name}.certificate_body}}}}"
            self.module.data[
                "certificate_chain"
            ] = f"${{{{module.{byo_cert_module.name}.certificate_chain}}}}"
        super(AzureK8sBaseProcessor, self).process(module_idx)
