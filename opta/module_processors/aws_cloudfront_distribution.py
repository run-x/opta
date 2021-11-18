from typing import TYPE_CHECKING

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsCloudfrontDstributionProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-cloudfront-distribution":
            raise Exception(
                f"The module {module.name} was expected to be of type aaws cloudfront distribution"
            )
        super(AwsCloudfrontDstributionProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        from_parent = False
        if len(aws_base_modules) == 0 and self.layer.parent is not None:
            from_parent = True
            aws_base_modules = self.layer.parent.get_module_by_type("aws-base")

        if len(aws_base_modules) == 0:
            logger.warn(
                "Did not find the aws-base module. "
                "This is highly recommended even for SPA as it sets up logging/auditing buckets"
            )
        else:
            module_source = (
                "data.terraform_remote_state.parent.outputs"
                if from_parent
                else f"module.{aws_base_modules[0].name}"
            )
            self.module.data["s3_log_bucket_name"] = self.module.data.get(
                "s3_log_bucket_name", f"${{{{{module_source}.s3_log_bucket_name}}}}"
            )

        links = self.module.data.get("links", [])
        for link in links:
            if isinstance(link, str):
                link = {link: {"access": "read"}}
            module_name = list(link.keys())[0]
            linked_module = self.layer.get_module(module_name, module_idx)
            if linked_module is None:
                raise UserErrors(f"Could not find module {module_name}")
            module_source = f"module.{linked_module.name}"
            self.module.data["bucket_name"] = f"${{{{{module_source}.bucket_id}}}}"

            access_type: str = link[module_name]["access"]
            if access_type not in ["read", "read_write", "read_write_delete"]:
                raise UserErrors(
                    "Invalid access type. Must be read, read_write, or read_write_delete"
                )
            if access_type == "read":
                self.module.data[
                    "origin_access_identity_path"
                ] = f"${{{{{module_source}.cloudfront_read_path}}}}"
            elif access_type == "read_write":
                self.module.data[
                    "origin_access_identity_path"
                ] = f"${{{{{module_source}.cloudfront_read_write_path}}}}"
            elif access_type == "read_write_delete":
                self.module.data[
                    "origin_access_identity_path"
                ] = f"${{{{{module_source}.cloudfront_read_write_delete_path}}}}"
            self.module.data["access_type"] = access_type
        super(AwsCloudfrontDstributionProcessor, self).process(module_idx)
