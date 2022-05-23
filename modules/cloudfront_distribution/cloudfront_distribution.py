from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class CloudfrontDistributionProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "cloudfront-distribution":
            raise Exception(
                f"The module {module.name} was expected to be of type aws cloudfront distribution"
            )
        super().__init__(module, layer)

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

        aws_dns_modules = self.layer.get_module_by_type("aws-dns", module_idx)
        if len(aws_dns_modules) != 0 and aws_dns_modules[0].data.get("linked_module") in [
            self.module.type,
            self.module.name,
        ]:
            aws_dns_module = aws_dns_modules[0]
            self.module.data["enable_auto_dns"] = True
            self.module.data["zone_id"] = (
                self.module.data.get("zone_id")
                or f"${{{{module.{aws_dns_module.name}.zone_id}}}}"
            )
            self.module.data["acm_cert_arn"] = (
                self.module.data.get("acm_cert_arn")
                or f"${{{{module.{aws_dns_module.name}.cert_arn}}}}"
            )
            self.module.data["domains"] = self.module.data.get("domains") or [
                f"${{{{module.{aws_dns_module.name}.domain}}}}"
            ]

        links = self.module.data.get("links", [])
        if links == [] and (
            "bucket_name" not in self.module.data
            or "origin_access_identity_path" not in self.module.data
        ):
            raise UserErrors(
                "You need to either link 1 opta s3 bucket or provide the bucket_name and "
                "origin_access_identity_path for your bucket."
            )

        if len(links) > 1:
            raise UserErrors("Cloudfront Distribution can't have more than one links.")

        for module_name in links:
            module = self.layer.get_module(module_name, module_idx)
            if module is None:
                raise UserErrors(f"Could not find module {module_name}")
            module_type = module.aliased_type or module.type
            if module_type == "aws-s3":
                self.handle_s3_link(module)
            elif module_type == "aws-k8s-base":
                self.handle_k8s_base_link(module)

        super(CloudfrontDistributionProcessor, self).process(module_idx)

    def handle_s3_link(self, linked_module: "Module") -> None:
        module_source = f"module.{linked_module.name}"
        self.module.data["bucket_name"] = f"${{{{{module_source}.bucket_id}}}}"
        self.module.data[
            "origin_access_identity_path"
        ] = f"${{{{{module_source}.cloudfront_read_path}}}}"
        self.module.data["s3_load_balancer_enabled"] = True

    def handle_k8s_base_link(self, linked_module: "Module") -> None:
        module_source = f"module.{linked_module.name}"
        self.module.data[
            "load_balancer_arn"
        ] = f"${{{{{module_source}.load_balancer_arn}}}}"
        self.module.data["eks_load_balancer_enabled"] = True
