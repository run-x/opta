from typing import Any, Optional

from opta.utils import all_substrings


class Resource:
    def __init__(self, parent_module: Any, tf_resource_type: str, name: str):
        self.parent_module = parent_module
        self.type = tf_resource_type
        self.name = name
        self.address = f"module.{parent_module.key}.{tf_resource_type}.{name}"
        self.inspect = self._get_inspect_config()

    def _get_inspect_config(self) -> Optional[dict]:
        # A module can configure an "inspect" field so that certain resources
        # are displayed during `opta inspect`
        module_inspect_config = self.parent_module.desc.get("inspect", {})

        # It could be possible that more than one inspect key matches the resource
        # address, ex. "helm_release" and "helm_release.k8s-service". Only return the
        # inspect config for the most specific/longest key.
        most_specific_inspect_key = ""
        for resource_inspect_key in module_inspect_config:
            if resource_inspect_key in all_substrings(self.address, "."):
                if len(resource_inspect_key) > len(most_specific_inspect_key):
                    most_specific_inspect_key = resource_inspect_key

        if most_specific_inspect_key == "":
            return None

        return module_inspect_config[most_specific_inspect_key]
