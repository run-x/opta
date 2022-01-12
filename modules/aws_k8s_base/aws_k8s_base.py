from typing import TYPE_CHECKING, Optional

import mypy_boto3_elbv2.type_defs
from kubernetes.client import CoreV1Api, V1ConfigMap
from mypy_boto3_elbv2 import ElasticLoadBalancingv2Client
from ruamel.yaml.compat import StringIO

from modules.base import AWSK8sModuleProcessor, K8sBaseModuleProcessor
from opta.core.aws import AWS
from opta.core.kubernetes import configure_kubectl, list_namespaces, load_opta_kube_config
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.utils import yaml

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsK8sBaseProcessor(AWSK8sModuleProcessor, K8sBaseModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-k8s-base":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s base"
            )
        super(AwsK8sBaseProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        byo_cert_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "external-ssl-cert":
                byo_cert_module = module
                break
        if byo_cert_module is not None:
            self.module.data[
                "private_key"
            ] = f"${{{{module.{byo_cert_module.name}.private_key}}}}"
            self.module.data[
                "certificate_body"
            ] = f"${{{{module.{byo_cert_module.name}.certificate_body}}}}"
            self.module.data[
                "certificate_chain"
            ] = f"${{{{module.{byo_cert_module.name}.certificate_chain}}}}"

        Terraform.download_state(self.layer)
        configure_kubectl(self.layer)
        self._process_nginx_extra_ports(self.module.data)

        aws_dns_module = None
        for module in self.layer.modules:
            if (module.aliased_type or module.type) == "aws-dns":
                aws_dns_module = module
                break
        if aws_dns_module is not None:
            self.module.data["domain"] = f"${{{{module.{aws_dns_module.name}.domain}}}}"
            self.module.data[
                "cert_arn"
            ] = f"${{{{module.{aws_dns_module.name}.cert_arn}}}}"

        aws_base_modules = self.layer.get_module_by_type("aws-base", module_idx)
        if len(aws_base_modules) == 0:
            raise UserErrors("Must have the base module in before the k8s-base")
        aws_base_module = aws_base_modules[0]
        self.module.data[
            "s3_log_bucket_name"
        ] = f"${{{{module.{aws_base_module.name}.s3_log_bucket_name}}}}"

        super(AwsK8sBaseProcessor, self).process(module_idx)

    def pre_hook(self, module_idx: int) -> None:
        Terraform.download_state(self.layer)
        configure_kubectl(self.layer)
        list_namespaces()
        super(AwsK8sBaseProcessor, self).pre_hook(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        if exception is not None:
            return
        self.add_admin_roles()

    def add_admin_roles(self) -> None:
        if self.module.data.get("admin_arns") is None:
            return
        Terraform.download_state(self.layer)
        configure_kubectl(self.layer)
        load_opta_kube_config()
        v1 = CoreV1Api()
        aws_auth_config_map: V1ConfigMap = v1.read_namespaced_config_map(
            "aws-auth", "kube-system"
        )
        opta_arns_config_map: V1ConfigMap = v1.read_namespaced_config_map(
            "opta-arns", "default"
        )
        admin_arns = yaml.load(opta_arns_config_map.data["adminArns"])
        current_data = aws_auth_config_map.data
        old_map_roles = yaml.load(current_data["mapRoles"])
        new_map_roles = [
            old_map_role
            for old_map_role in old_map_roles
            if not old_map_role["username"].startswith("opta-managed")
        ]
        old_map_users = yaml.load(current_data.get("mapUsers", "[]"))
        new_map_users = [
            old_map_user
            for old_map_user in old_map_users
            if not old_map_user["username"].startswith("opta-managed")
        ]
        for arn in admin_arns:
            arn_data = AWS.parse_arn(arn)
            if arn_data["resource_type"] == "user":
                new_map_users.append(
                    {
                        "groups": ["system:masters"],
                        "userarn": arn,
                        "username": "opta-managed",
                    }
                )
            elif arn_data["resource_type"] == "role":
                new_map_roles.append(
                    {
                        "groups": ["system:masters"],
                        "rolearn": arn,
                        "username": "opta-managed",
                    }
                )
            else:
                raise UserErrors(f"Invalid arn for IAM role or user: {arn}")
        stream = StringIO()
        yaml.dump(new_map_roles, stream)
        aws_auth_config_map.data["mapRoles"] = stream.getvalue()
        if len(new_map_users) > 0:
            stream = StringIO()
            yaml.dump(new_map_users, stream)
            aws_auth_config_map.data["mapUsers"] = stream.getvalue()
        v1.replace_namespaced_config_map(
            "aws-auth", "kube-system", body=aws_auth_config_map
        )

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
