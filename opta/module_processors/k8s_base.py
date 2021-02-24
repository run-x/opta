from typing import TYPE_CHECKING

from opta.module_processors.base import K8sModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class K8sBaseProcessor(K8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(K8sBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_dns_module = None
        for module in self.layer.modules:
            if module.data["type"] == "aws-dns":
                aws_dns_module = module
                break
        if aws_dns_module is not None:
            self.module.data["domain"] = f"${{{{module.{aws_dns_module.name}.domain}}}}"
            self.module.data[
                "cert_arn"
            ] = f"${{{{module.{aws_dns_module.name}.cert_arn}}}}"
        super(K8sBaseProcessor, self).process(module_idx)
