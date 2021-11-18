from typing import TYPE_CHECKING

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsCloudfrontDstributionProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "cloudfront-distribution":
            raise Exception(
                f"The module {module.name} was expected to be of type aws cloudfront distribution"
            )
        super(AwsCloudfrontDstributionProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        from_parent = False
        if len(aws_base_modules) == 0 and self.layer.parent is not None:
            from_parent = True
            aws_base_modules = self.layer.parent.get_module_by_type("aws-base")

        if len(aws_base_modules) == 0:
            logger.debug(
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
        if links == [] and (
            "bucket_name" not in self.module.data
            or "origin_access_identity_path" not in self.module.data
        ):
            raise UserErrors(
                "You need to either link 1 opta s3 bucket or provide the bucket_name and "
                "origin_access_identity_path for your bucket."
            )

        for module_name in links:
            linked_module = self.layer.get_module(module_name, module_idx)
            if linked_module is None:
                raise UserErrors(f"Could not find module {module_name}")
            module_source = f"module.{linked_module.name}"
            self.module.data["bucket_name"] = f"${{{{{module_source}.bucket_id}}}}"
            self.module.data[
                "origin_access_identity_path"
            ] = f"${{{{{module_source}.cloudfront_read_path}}}}"

        super(AwsCloudfrontDstributionProcessor, self).process(module_idx)
