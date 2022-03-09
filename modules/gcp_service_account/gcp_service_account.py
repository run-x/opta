from typing import TYPE_CHECKING, List

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class GcpServiceAccountProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        super(GcpServiceAccountProcessor, self).__init__(module, layer)

    def handle_gcs_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(
                    f"${{{{module.{linked_module.name}.bucket_name}}}}"
                )
            elif permission == "write":
                self.write_buckets.append(
                    f"${{{{module.{linked_module.name}.bucket_name}}}}"
                )
            else:
                raise Exception(f"Invalid permission {permission}")

    def process(self, module_idx: int) -> None:
        # Handle links
        for link_data in self.module.data.get("links", []):
            if type(link_data) is str:
                target_module_name = link_data
                link_permissions = []
            elif type(link_data) is dict:
                target_module_name = list(link_data.keys())[0]
                link_permissions = list(link_data.values())[0]
            else:
                raise UserErrors(
                    f"Link data {link_data} must be a string or map holding the permissions"
                )
            module = self.layer.get_module(target_module_name, module_idx)
            if module is None:
                raise Exception(
                    f"Did not find the desired module {target_module_name} "
                    "make sure that the module you're referencing is listed before the k8s "
                    "app one"
                )
            module_type = module.aliased_type or module.type
            if module_type == "gcp-gcs":
                self.handle_gcs_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for gcp service account link: {module_type}"
                )

        self.module.data["read_buckets"] = (
            self.module.data.get("read_buckets", []) + self.read_buckets
        )
        self.module.data["write_buckets"] = (
            self.module.data.get("write_buckets", []) + self.write_buckets
        )
        super(GcpServiceAccountProcessor, self).process(module_idx)
