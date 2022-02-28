from time import sleep
from typing import TYPE_CHECKING, Dict, List, Optional

import boto3
from botocore.config import Config
from mypy_boto3_autoscaling import AutoScalingClient
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.type_defs import NetworkInterfaceTypeDef
from mypy_boto3_logs import CloudWatchLogsClient

from modules.base import ModuleProcessor
from opta.core.kubernetes import cluster_exist, get_cluster_name, purge_opta_kube_config
from opta.exceptions import UserErrors
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

    def post_delete(self, module_idx: int) -> None:
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        self.cleanup_cloudwatch_log_group(region)
        self.cleanup_dangling_enis(region)
        self.cleanup_security_groups(region)
        purge_opta_kube_config(layer=self.layer)

    def pre_hook(self, module_idx: int) -> None:
        if cluster_exist(self.layer.root()):
            return
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        self.cleanup_cloudwatch_log_group(region)

    def cleanup_security_groups(self, region: str) -> None:
        logger.debug("Seeking dangling security groups EKS forgot to destroy.")
        client: EC2Client = boto3.client("ec2", config=Config(region_name=region))
        vpcs = client.describe_vpcs(
            Filters=[
                {"Name": "tag:layer", "Values": [self.layer.name]},
                {"Name": "tag:opta", "Values": ["true"]},
            ]
        )["Vpcs"]
        if len(vpcs) == 0:
            logger.debug(f"Opta vpc for layer {self.layer.name} not found")
            return
        elif len(vpcs) > 1:
            logger.debug(
                f"Weird, found multiple vpcs for layer {self.layer.name}: {[x['VpcId'] for x in vpcs]}"
            )
            return
        vpc = vpcs[0]
        vpc_id = vpc["VpcId"]
        eks_security_groups = client.describe_security_groups(
            Filters=[
                {
                    "Name": f"tag:kubernetes.io/cluster/opta-{self.layer.name}",
                    "Values": ["owned"],
                },
                {"Name": "vpc-id", "Values": [vpc_id]},
            ],
        )["SecurityGroups"]
        if len(eks_security_groups) == 0:
            logger.debug("No dangling security groups found")
            return
        for eks_security_group in eks_security_groups:
            logger.debug(
                f"Deleting dangling security group {eks_security_group['GroupId']}"
            )
            client.delete_security_group(GroupId=eks_security_group["GroupId"])

    def cleanup_cloudwatch_log_group(self, region: str) -> None:
        logger.debug(
            "Seeking dangling cloudwatch log group for k8s cluster just destroyed."
        )
        client: CloudWatchLogsClient = boto3.client(
            "logs", config=Config(region_name=region)
        )
        log_group_name = f"/aws/eks/opta-{self.layer.name}/cluster"
        log_groups = client.describe_log_groups(logGroupNamePrefix=log_group_name)
        if len(log_groups["logGroups"]) == 0:
            return
        logger.debug(
            f"Found dangling cloudwatch log group {log_group_name}. Deleting it now"
        )
        client.delete_log_group(logGroupName=log_group_name)
        sleep(3)
        log_groups = client.describe_log_groups(logGroupNamePrefix=log_group_name)
        if len(log_groups["logGroups"]) != 0:
            logger.warning(
                f"Cloudwatch Log group {log_group_name} has recreated itself. Not stopping the destroy, but you will "
                "wanna check this out."
            )

    def cleanup_dangling_enis(self, region: str) -> None:
        client: EC2Client = boto3.client("ec2", config=Config(region_name=region))
        vpcs = client.describe_vpcs(
            Filters=[
                {"Name": "tag:layer", "Values": [self.layer.name]},
                {"Name": "tag:opta", "Values": ["true"]},
            ]
        )["Vpcs"]
        if len(vpcs) == 0:
            logger.debug(f"Opta vpc for layer {self.layer.name} not found")
            return
        elif len(vpcs) > 1:
            logger.debug(
                f"Weird, found multiple vpcs for layer {self.layer.name}: {[x['VpcId'] for x in vpcs]}"
            )
            return
        vpc = vpcs[0]
        vpc_id = vpc["VpcId"]
        dangling_enis: List[NetworkInterfaceTypeDef] = []
        next_token = None
        logger.debug("Seeking dangling enis from k8s cluster just destroyed")
        while True:
            if next_token is None:
                describe_enis = client.describe_network_interfaces(
                    Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
                )
            else:
                describe_enis = client.describe_network_interfaces(  # type: ignore
                    Filters=[{"Name": "vpc-id", "Values": [vpc_id]}], NextToken=next_token
                )
            for eni in describe_enis["NetworkInterfaces"]:
                if eni["Description"] == f"Amazon EKS opta-{self.layer.name}" or (
                    eni["Description"].startswith("aws-K8S")
                    and eni["Status"] == "available"
                ):
                    logger.debug(
                        f"Identified dangling EKS network interface {eni['NetworkInterfaceId']}"
                    )
                    dangling_enis.append(eni)
            next_token = describe_enis.get("NextToken", None)
            if next_token is None:
                break
        for eni in dangling_enis:
            logger.debug(
                f"Now deleting dangling network interface {eni['NetworkInterfaceId']}"
            )
            client.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])

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
            if current_token == "":  # nosec
                break

    def process(self, module_idx: int) -> None:
        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        if len(aws_base_modules) == 0:
            raise UserErrors(
                "Could not find aws base module in this opta yaml-- you need to have it for eks to work"
            )
        aws_base_module = aws_base_modules[0]
        self.module.data["cluster_name"] = get_cluster_name(self.layer.root())
        self.module.data[
            "private_subnet_ids"
        ] = f"${{{{module.{aws_base_module.name}.private_subnet_ids}}}}"
        self.module.data[
            "kms_account_key_arn"
        ] = f"${{{{module.{aws_base_module.name}.kms_account_key_arn}}}}"
        self.module.data["vpc_id"] = f"${{{{module.{aws_base_module.name}.vpc_id}}}}"
        super(AwsEksProcessor, self).process(module_idx)
