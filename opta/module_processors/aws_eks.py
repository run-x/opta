from typing import TYPE_CHECKING, Dict, Optional

import boto3
from botocore.config import Config
from mypy_boto3_autoscaling import AutoScalingClient

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsEksProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-eks":
            raise Exception(
                f"The module {module.name} was expected to be of type aws eks"
            )
        super(AwsEksProcessor, self).__init__(module, layer)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        if exception is not None or not self.module.data.get("enable_metrics", False):
            logger.debug(
                "Not enabling metrics for default node group's autoscaling group"
            )
            return
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        autoscaling_client: AutoScalingClient = boto3.client(
            "autoscaling", config=Config(region_name=region)
        )
        kwargs: Dict[str, str] = {}
        while True:
            response = autoscaling_client.describe_auto_scaling_groups(
                **kwargs  # type: ignore
            )
            current_token = response.get("NextToken", "")
            kwargs["NextToken"] = current_token
            current_groups = response["AutoScalingGroups"]
            cluster_name = f"opta-{self.layer.root().name}"
            for group in current_groups:
                tag_dict = {x["Key"]: x["Value"] for x in group["Tags"]}
                if tag_dict.get(
                    f"kubernetes.io/cluster/{cluster_name}"
                ) == "owned" and tag_dict.get("eks:nodegroup-name", "").startswith(
                    f"{cluster_name}-default"
                ):
                    group_name = group["AutoScalingGroupName"]
                    logger.debug(f"Enabling metrics for autoscaling group {group_name}")
                    autoscaling_client.enable_metrics_collection(
                        AutoScalingGroupName=group_name, Granularity="1Minute"
                    )
                return None
            if current_token == "":
                break

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        if len(aws_base_modules) == 0:
            raise UserErrors(
                "Could not find aws base module in this opta yaml-- you need to have it for eks to work"
            )
        aws_base_module = aws_base_modules[0]
        self.module.data[
            "private_subnet_ids"
        ] = f"${{{{module.{aws_base_module.name}.private_subnet_ids}}}}"
        self.module.data[
            "kms_account_key_arn"
        ] = f"${{{{module.{aws_base_module.name}.kms_account_key_arn}}}}"
        super(AwsEksProcessor, self).process(module_idx)
