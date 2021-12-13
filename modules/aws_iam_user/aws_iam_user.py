from typing import TYPE_CHECKING

from modules.base import AWSIamAssembler, ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsIamUserProcessor(ModuleProcessor, AWSIamAssembler):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "aws-iam-user":
            raise Exception(
                f"The module {module.name} was expected to be of type aws iam user"
            )
        super(AwsIamUserProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.handle_iam_policy(module_idx)
        super(AwsIamUserProcessor, self).process(module_idx)

    def handle_iam_policy(self, module_idx: int) -> None:
        iam_statements = [
            {
                "Sid": "AllowViewAccountInfo",
                "Action": ["iam:GetAccountPasswordPolicy", "iam:GetAccountSummary"],
                "Effect": "Allow",
                "Resource": ["*"],
            },
            {
                "Sid": "AllowManageOwnPasswords",
                "Effect": "Allow",
                "Action": ["iam:ChangePassword", "iam:GetUser"],
                "Resource": "arn:aws:iam::*:user/$${{aws:username}}",
            },
            {
                "Sid": "AllowManageOwnAccessKeys",
                "Effect": "Allow",
                "Action": [
                    "iam:CreateAccessKey",
                    "iam:DeleteAccessKey",
                    "iam:ListAccessKeys",
                    "iam:UpdateAccessKey",
                ],
                "Resource": "arn:aws:iam::*:user/$${{aws:username}}",
            },
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
            elif module_type == "aws-sqs":
                self.handle_sqs_link(module, link_permissions)
            elif module_type == "aws-sns":
                self.handle_sns_link(module, link_permissions)
            elif module_type == "aws-dynamodb":
                self.handle_dynamodb_link(module, link_permissions)
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )
        iam_statements += self.prepare_iam_statements()
        self.module.data["iam_policy"] = {
            "Version": "2012-10-17",
            "Statement": iam_statements,
        }
