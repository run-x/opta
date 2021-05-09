from typing import TYPE_CHECKING, List

from opta.core.aws import AWS
from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor, get_eks_module_refs

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsIamRoleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "aws-iam-role":
            raise Exception(
                f"The module {module.name} was expected to be of type aws iam role"
            )
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        super(AwsIamRoleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.handle_iam_policy(module_idx)
        self.handle_k8s_trusts(module_idx)
        if (
            self.module.data.get("allowed_k8s_services", []) == []
            and self.module.data.get("allowed_iams", []) == []
        ):
            raise UserErrors(
                "AWS Iam role needs to trust either a k8s service or some other role or user."
            )
        super(AwsIamRoleProcessor, self).process(module_idx)

    def handle_k8s_trusts(self, module_idx: int) -> None:
        allowed_k8s_services = self.module.data.get("allowed_k8s_services", [])
        if allowed_k8s_services != []:
            eks_module_refs = get_eks_module_refs(self.layer, module_idx)
            self.module.data["kubernetes_trusts"] = [
                {
                    "open_id_url": eks_module_refs[0],
                    "open_id_arn": eks_module_refs[1],
                    "service_name": allowed_k8s_service["service_name"],
                    "namespace": allowed_k8s_service["namespace"],
                }
                for allowed_k8s_service in allowed_k8s_services
            ]

    def handle_iam_policy(self, module_idx: int) -> None:
        iam_statements = [
            {
                "Sid": "PolicySimulatorAPI",
                "Action": [
                    "iam:GetContextKeysForCustomPolicy",
                    "iam:GetContextKeysForPrincipalPolicy",
                    "iam:SimulateCustomPolicy",
                    "iam:SimulatePrincipalPolicy",
                ],
                "Effect": "Allow",
                "Resource": "*",
            },
            {
                "Sid": "PolicySimulatorConsole",
                "Action": [
                    "iam:GetGroup",
                    "iam:GetGroupPolicy",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:GetRole",
                    "iam:GetRolePolicy",
                    "iam:GetUser",
                    "iam:GetUserPolicy",
                    "iam:ListAttachedGroupPolicies",
                    "iam:ListAttachedRolePolicies",
                    "iam:ListAttachedUserPolicies",
                    "iam:ListGroups",
                    "iam:ListGroupPolicies",
                    "iam:ListGroupsForUser",
                    "iam:ListRolePolicies",
                    "iam:ListRoles",
                    "iam:ListUserPolicies",
                    "iam:ListUsers",
                ],
                "Effect": "Allow",
                "Resource": "*",
            },
        ]
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
            module_type = module.data["type"]
            # TODO: Add support for SNS, SQS, KINESIS,
            if module_type == "aws-s3":
                self.handle_s3_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )
        if self.read_buckets:
            iam_statements.append(
                AWS.prepare_read_buckets_iam_statements(self.read_buckets)
            )
        if self.write_buckets:
            iam_statements.append(
                AWS.prepare_write_buckets_iam_statements(self.write_buckets)
            )
        self.module.data["iam_policy"] = {
            "Version": "2012-10-17",
            "Statement": iam_statements,
        }

    def handle_s3_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        bucket_name = linked_module.data["bucket_name"]
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(bucket_name)
            elif permission == "write":
                self.write_buckets.append(bucket_name)
            else:
                raise Exception(f"Invalid permission {permission}")
