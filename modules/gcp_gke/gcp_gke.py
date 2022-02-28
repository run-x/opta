from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.core.gcp import GCP
from opta.core.kubernetes import get_cluster_name, purge_opta_kube_config
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpGkeProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GcpGkeProcessor, self).__init__(module, layer)

    def post_delete(self, module_idx: int) -> None:
        purge_opta_kube_config(layer=self.layer)

    def process(self, module_idx: int) -> None:
        gcp_base_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "gcp-base":
                gcp_base_module = module
                break
        if gcp_base_module is None:
            raise UserErrors(
                "The gcp-gke module needs to be run on the same yaml as the gcp-base"
            )
        self.module.data["cluster_name"] = get_cluster_name(self.layer.root())
        self.module.data[
            "vpc_self_link"
        ] = f"${{{{module.{gcp_base_module.name}.vpc_self_link}}}}"
        self.module.data[
            "private_subnet_self_link"
        ] = f"${{{{module.{gcp_base_module.name}.private_subnet_self_link}}}}"
        self.module.data[
            "k8s_master_ipv4_cidr_block"
        ] = f"${{{{module.{gcp_base_module.name}.k8s_master_ipv4_cidr_block}}}}"
        self.module.data["node_zone_names"] = GCP(self.layer).get_current_zones()
        super(GcpGkeProcessor, self).process(module_idx)
