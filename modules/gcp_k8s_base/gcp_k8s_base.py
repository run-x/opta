from typing import TYPE_CHECKING

from modules.base import GcpK8sModuleProcessor
from opta.core.gcp import GCP

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpK8sBaseProcessor(GcpK8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "gcp-k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(GcpK8sBaseProcessor, self).__init__(module, layer)

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

        gcp_dns_modules = self.layer.get_module_by_type("gcp-dns", module_idx)
        gcp_dns_module = None
        if len(gcp_dns_modules) > 0:
            gcp_dns_module = gcp_dns_modules[0]
        if gcp_dns_module is not None:
            self.module.data[
                "hosted_zone_name"
            ] = f"${{{{module.{gcp_dns_module.name}.zone_name}}}}"
            self.module.data["domain"] = f"${{{{module.{gcp_dns_module.name}.domain}}}}"
            self.module.data[
                "cert_self_link"
            ] = f"${{{{module.{gcp_dns_module.name}.cert_self_link}}}}"
            self.module.data[
                "delegated"
            ] = f"${{{{module.{gcp_dns_module.name}.delegated}}}}"
        self.module.data["zone_names"] = GCP(self.layer).get_current_zones()
        super(GcpK8sBaseProcessor, self).process(module_idx)
