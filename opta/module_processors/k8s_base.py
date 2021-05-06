from typing import TYPE_CHECKING, Optional

import boto3
import mypy_boto3_elbv2.type_defs
from botocore.config import Config
from mypy_boto3_elbv2 import ElasticLoadBalancingv2Client

from opta.module_processors.base import AWSK8sModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class K8sBaseProcessor(AWSK8sModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(K8sBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        aws_dns_module = None
        for module in self.layer.modules:
            if module.data["type"] == "aws-dns":
                aws_dns_module = module
                break
        if aws_dns_module is not None:
            self.module.data["domain"] = f"${{{{module.{aws_dns_module.name}.domain}}}}"
            self.module.data[
                "cert_arn"
            ] = f"${{{{module.{aws_dns_module.name}.cert_arn}}}}"
        super(K8sBaseProcessor, self).process(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        # Manually set the AlpnPolicy to HTTP2Preferred cause the damn K8s service annotation doesn't do its job.
        if exception is not None:
            return
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        client: ElasticLoadBalancingv2Client = boto3.client(
            "elbv2", config=Config(region_name=region)
        )
        current_load_balancer = self._get_load_balancer(client)
        if current_load_balancer is not None:
            listeners = client.describe_listeners(
                LoadBalancerArn=current_load_balancer["LoadBalancerArn"]
            )
            for listener in listeners["Listeners"]:
                if listener["Port"] == 443:
                    client.modify_listener(
                        ListenerArn=listener["ListenerArn"], AlpnPolicy=["HTTP2Preferred"]
                    )
                    return

    def _get_load_balancer(
        self, client: ElasticLoadBalancingv2Client
    ) -> Optional[mypy_boto3_elbv2.type_defs.LoadBalancerTypeDef]:
        marker = ""
        while True:
            output = client.describe_load_balancers(Marker=marker)
            marker = output.get("NextMarker", "")
            load_balancers = output["LoadBalancers"]
            current_arns = [x["LoadBalancerArn"] for x in load_balancers]
            arn_to_lb = {x["LoadBalancerArn"]: x for x in load_balancers}
            tag_descriptions = client.describe_tags(ResourceArns=current_arns)[
                "TagDescriptions"
            ]
            cluster_name = f"opta-{self.layer.root().name}"
            for idx, tag_description in enumerate(tag_descriptions):
                tag_dict = {d["Key"]: d["Value"] for d in tag_description["Tags"]}

                if (
                    tag_dict.get(f"kubernetes.io/cluster/{cluster_name}") == "owned"
                    and tag_dict.get("kubernetes.io/service-name")
                    == "ingress-nginx/ingress-nginx-controller"
                ):
                    return arn_to_lb[tag_description["ResourceArn"]]

            if marker == "":
                break
        return None
