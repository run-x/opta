from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GlobalAcceleratorsProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GlobalAcceleratorsProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_dns_modules = self.layer.get_module_by_type("aws-dns")
        if len(aws_dns_modules) != 0 and aws_dns_modules[0].data.get("linked_module") in [
            self.module.type,
            self.module.name,
        ]:
            aws_dns_module = aws_dns_modules[0]
            self.module.data["enable_auto_dns"] = True
            self.module.data["domain"] = (
                self.module.data.get("domain")
                or f"${{{{module.{aws_dns_module.name}.domain}}}}"
            )
            self.module.data["zone_id"] = (
                self.module.data.get("zone_id")
                or f"${{{{module.{aws_dns_module.name}.zone_id}}}}"
            )

        if (self.module.data.get("domain") is None) != (
            self.module.data.get("zone_id") is None
        ):
            raise UserErrors(
                "Either both domain and zone_id are mentioned at the same time, or none at all."
            )
        k8s_base_modules = self.layer.get_module_by_type("k8s-base", module_idx)
        if len(k8s_base_modules) != 0:
            k8s_base_module = k8s_base_modules[0]
            self.module.data["endpoint_id"] = (
                self.module.data.get("endpoint_id")
                or f"${{{{module.{k8s_base_module.name}.load_balancer_arn}}}}"
            )
        super(GlobalAcceleratorsProcessor, self).process(module_idx)
