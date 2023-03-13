from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.core.gcp import GCP
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpNodePoolProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GcpNodePoolProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        if "guest_accelerators" in self.module.data:
            gcp_gke_module = None
            for module in self.layer.modules:
                if (module.aliased_type or module.type) == "gcp-gke":
                    gcp_gke_module = module
                    break
            if gcp_gke_module is None:
                raise UserErrors(
                    "The gcp-nodepool module needs to be run on the same yaml as gcp-gke"
                )
            gcp_gke_node_zone_names = set(gcp_gke_module.data["node_zone_names"])
            guest_accelerator_types = [
                ga["type"] for ga in self.module.data["guest_accelerators"]
            ]
            # Identify the intersection of the GKE cluster's node locations, and zones
            # where the desired guest accelerators are available.
            gcp_nodepool_node_zone_names = sorted(
                set(
                    GCP(self.layer).get_zones_for_accelerator_types(
                        *guest_accelerator_types
                    )
                )
                & gcp_gke_node_zone_names
            )
            # Since the gcp-gke module does not know about required guest accelerators,
            # it may choose zones where the desired guest accelerators are not
            # available. We should really be smarter about picking zones, but for now,
            # just throw an error is an overlap cannot be determined.
            if not gcp_nodepool_node_zone_names:
                raise UserErrors(
                    f"Desired guest accelerators not available in cluster node locations: {', '.join(gcp_gke_node_zone_names)}"
                )
            self.module.data["node_zone_names"] = gcp_nodepool_node_zone_names
        super(GcpNodePoolProcessor, self).process(module_idx)
