# type: ignore
import os

from pytest_mock import MockFixture

from opta.layer import Layer
from opta.module_processors.aws_iam_user import AwsIamUserProcessor


class TestAwsIamUserProcessor:
    def test_process(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("deployeruser", 8)
        mocked_handle_iam_policy = mocker.patch(
            "opta.module_processors.aws_iam_user.AwsIamUserProcessor.handle_iam_policy"
        )
        AwsIamUserProcessor(app_module, layer).process(8)
        mocked_handle_iam_policy.assert_called_once_with(8)

    def test_handle_iam_policy(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("deployeruser", 8)
        processor = AwsIamUserProcessor(app_module, layer)
        processor.handle_iam_policy(module_idx=8)
        assert processor.module.data["iam_policy"]["Statement"] == [
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
                "Resource": "arn:aws:iam::*:user/${aws:username}",
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
                "Resource": "arn:aws:iam::*:user/${aws:username}",
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
            {
                "Sid": "ReadBuckets",
                "Action": ["s3:GetObject*", "s3:ListBucket"],
                "Effect": "Allow",
                "Resource": ["arn:aws:s3:::bucket2", "arn:aws:s3:::bucket2/*"],
            },
            {
                "Sid": "WriteBuckets",
                "Action": [
                    "s3:GetObject*",
                    "s3:PutObject*",
                    "s3:DeleteObject*",
                    "s3:ListBucket",
                ],
                "Effect": "Allow",
                "Resource": ["arn:aws:s3:::bucket1", "arn:aws:s3:::bucket1/*"],
            },
        ]
