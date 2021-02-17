import os
from typing import Any, Dict, List

import hcl2

from opta.constants import REGISTRY
from opta.resource import Resource


class Module:
    def __init__(
        self, layer_name: str, key: str, data: Dict[Any, Any], parent_layer: Any = None
    ):
        self.layer_name = layer_name
        self.key = key
        self.data = data
        self.parent_layer = parent_layer
        self.desc = REGISTRY["modules"][data["type"]]
        self.name = f"{layer_name}-{self.key}"
        self.terraform_resources: Any = None

    def gen_tf(self) -> Dict[Any, Any]:
        module_blk: Dict[Any, Any] = {
            "module": {
                self.key: {"source": self.translate_location(self.desc["location"])}
            },
            "output": {},
        }

        for k, v in self.desc["variables"].items():
            if k in self.data:

                # If a user specifies AUTO in their k8s config, let our terrform module
                # automatically derive their ECR repo
                if self.data["type"] == "k8s-service" and k == "image" and v == "AUTO":
                    continue

                module_blk["module"][self.key][k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "name":
                module_blk["module"][self.key][k] = self.name
            elif k == "module_name":
                module_blk["module"][self.key][k] = self.key
            elif k == "layer_name":
                module_blk["module"][self.key][k] = self.layer_name
            elif self.parent_layer is not None and k in self.parent_layer.outputs():
                module_blk["module"][self.key][
                    k
                ] = f"${{{{data.terraform_remote_state.parent.outputs.{k} }}}}"
            else:
                raise Exception(f"Unable to hydrate {k}")

        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if "export" in v and v["export"]:
                    module_blk["output"].update(
                        {k: {"value": f"${{{{module.{self.key}.{k} }}}}"}}
                    )

        return module_blk

    def translate_location(self, loc: str) -> str:
        relative_path = os.path.relpath(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "tf_modules", loc
            ),
            os.getcwd(),
        )
        # Note: This breaks should runxc ever be prefixed with "."
        if "." != relative_path[0]:
            relative_path = f"./{relative_path}"

        return relative_path

    def get_terraform_resources(self) -> List[Resource]:
        # Reading and extracting resources from terraform HCL files can be
        # time-consuming, so only do it once if necessary (for the inspect command).
        if self.terraform_resources is not None:
            return self.terraform_resources

        self.terraform_resources = self._read_terraform_resources()
        return self.terraform_resources

    def _read_terraform_resources(self) -> List[Resource]:
        tf_module_dir = self.translate_location(self.desc["location"])
        # Get all of the (non-nested) terraform files in the current module.
        tf_files = [
            entry for entry in os.scandir(tf_module_dir) if entry.path.endswith(".tf")
        ]

        terraform_resources: List[Resource] = []
        # Read and extract the resources from each current terraform file.
        for tf_file in tf_files:
            tf_config = hcl2.load(open(tf_file))
            tf_resources = tf_config.get("resource", [])
            for resource in tf_resources:
                resource_type = list(resource.keys())[0]
                resource_name = list(resource[resource_type].keys())[0]
                resource = Resource(self, resource_type, resource_name)
                terraform_resources.append(resource)

        return terraform_resources
