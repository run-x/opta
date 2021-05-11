import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional

import hcl2

from opta.constants import REGISTRY
from opta.exceptions import UserErrors
from opta.resource import Resource
from opta.utils import deep_merge

TAGS_OVERRIDE_FILE = "tags_override.tf.json"


class Module:
    def __init__(self, layer_name: str, data: Dict[Any, Any], parent_layer: Any = None):
        if "type" not in data:
            raise UserErrors("Module data must always have a type")
        self.type = data["type"]
        self.layer_name = layer_name
        self.data = data
        self.parent_layer = parent_layer
        self.name = data.get("name", self.type.replace("-", ""))
        if not Module.valid_name(self.name):
            raise UserErrors("Invalid module name, can only contain letters and numbers!")
        self.desc = REGISTRY["modules"][self.type]
        self.halt = REGISTRY["modules"][self.type].get("halt", False)
        self.module_dir_path = self.translate_location(self.desc["location"])

    def outputs(self) -> Iterable[str]:
        ret = []
        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if "export" in v and v["export"]:
                    ret.append(k)
        return ret

    @staticmethod
    def valid_name(name: str) -> bool:
        pattern = "^[A-Za-z0-9]*$"
        return bool(re.match(pattern, name))

    def gen_tf(self, depends_on: Optional[List[str]] = None) -> Dict[Any, Any]:
        if self.module_dir_path == "":
            return {}
        module_blk: Dict[Any, Any] = {
            "module": {self.name: {"source": self.module_dir_path}},
            "output": {},
        }
        for k, v in self.desc["variables"].items():
            if k in self.data:
                module_blk["module"][self.name][k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "module_name":
                module_blk["module"][self.name][k] = self.name
            elif k == "layer_name":
                module_blk["module"][self.name][k] = self.layer_name
            else:
                raise Exception(f"Unable to hydrate {k}")

        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if "export" in v and v["export"]:
                    entry: Dict[Any, Any] = {"value": f"${{{{module.{self.name}.{k} }}}}"}
                    if v.get("sensitive", False):
                        entry["sensitive"] = True
                    module_blk["output"].update({k: entry})
        if depends_on is not None:
            module_blk["module"][self.name]["depends_on"] = depends_on

        # If there are no outputs, don't set the output key. Terraform doesn't like an
        # empty output block.
        if module_blk["output"] == {}:
            del module_blk["output"]

        return module_blk

    # Generate an override file in the module, that adds extra tags to every resource.
    def gen_tags_override(self) -> None:
        override_config: Any = {"resource": []}

        resources = self.get_terraform_resources()
        for resource in resources:
            resource_tags_raw = resource.tf_config.get("tags", {})
            resource_tags = {}
            [resource_tags.update(tag) for tag in resource_tags_raw]

            # Add additional tags to each AWS resource
            resource_tags = deep_merge(
                resource_tags,
                {
                    "opta": "true",
                    "layer": self.layer_name,
                    "tf_address": f"module.{self.name}.{resource.type}.{resource.name}",
                },
            )

            override_config["resource"].append(
                {resource.type: {resource.name: {"tags": resource_tags}}}
            )
        if override_config["resource"] == []:
            return

        with open(f"{self.module_dir_path}/{TAGS_OVERRIDE_FILE}", "w") as f:
            json.dump(override_config, f, ensure_ascii=False, indent=2)

    def translate_location(self, loc: str) -> str:
        if loc == "":
            return ""
        relative_path = os.path.relpath(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "tf_modules", loc
            ),
            os.getcwd(),
        )

        # Terraform requires the module paths to be relative so add a ./ when
        # that's not the output of os.path.relpath
        if not (relative_path.startswith("./") or relative_path.startswith("../")):
            relative_path = f"./{relative_path}"

        return relative_path

    # Get the list of resources created by the current module.
    def get_terraform_resources(self) -> List[Resource]:
        if self.module_dir_path == "":
            return []
        tf_config = self._read_tf_module_config()
        terraform_resources: List[Resource] = []
        for _, tf_file_config in tf_config.items():
            tf_resources = tf_file_config.get("resource", [])
            for resource in tf_resources:
                resource_type = list(resource.keys())[0]
                resource_name = list(resource[resource_type].keys())[0]
                resource_config = resource[resource_type][resource_name]
                resource = Resource(self, resource_type, resource_name, resource_config)
                terraform_resources.append(resource)

        return terraform_resources

    # Read all terraform files in the module and return its contents as a single dict.
    def _read_tf_module_config(self) -> dict:
        tf_module_config = {}

        # Get all of the (non-nested) terraform files in the current module.
        tf_files = [
            entry
            for entry in os.scandir(self.module_dir_path)
            if entry.path.endswith(".tf")
        ]

        # Read and parse each terraform file.
        for tf_file in tf_files:
            tf_file_config = hcl2.load(open(tf_file))
            tf_module_config[tf_file.name] = tf_file_config

        return tf_module_config
