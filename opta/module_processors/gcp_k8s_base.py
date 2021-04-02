from typing import TYPE_CHECKING

from opta.module_processors.base import GcpK8sModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpK8sBaseProcessor(GcpK8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "gcp-k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(GcpK8sBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        gcp_dns_module = None
        for module in self.layer.modules:
            if module.data["type"] == "gcp-dns":
                gcp_dns_module = module
                break
        if gcp_dns_module is not None:
            self.module.data[
                "hosted_zone_name"
            ] = f"${{{{module.{gcp_dns_module.name}.zone_name}}}}"
            self.module.data[
                "cert_self_link"
            ] = f"${{{{module.{gcp_dns_module.name}.cert_self_link}}}}"
            self.module.data[
                "delegated"
            ] = f"${{{{module.{gcp_dns_module.name}.delegated}}}}"
        super(GcpK8sBaseProcessor, self).process(module_idx)
