# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from modules.aws_iam_role.aws_iam_role import AwsIamRoleProcessor
from opta.exceptions import UserErrors
from opta.layer import Layer


class TestAwsIamRoleProcessor:
    def test_process(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        app_module = layer.get_module("deployerrole", 8)
        mocked_handle_iam_policy = mocker.patch(
            "modules.aws_iam_role.aws_iam_role.AwsIamRoleProcessor.handle_iam_policy"
        )
        mocked_handle_k8s_trusts = mocker.patch(
            "modules.aws_iam_role.aws_iam_role.AwsIamRoleProcessor.handle_k8s_trusts"
        )
        AwsIamRoleProcessor(app_module, layer).process(8)
        mocked_handle_iam_policy.assert_called_once_with(8)
        mocked_handle_k8s_trusts.assert_called_once_with(8)

    def test_process_no_trusts(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        app_module = layer.get_module("deployerrole", 8)
        del app_module.data["allowed_iams"]
        del app_module.data["allowed_k8s_services"]
        mocked_handle_iam_policy = mocker.patch(
            "modules.aws_iam_role.aws_iam_role.AwsIamRoleProcessor.handle_iam_policy"
        )
        mocked_handle_k8s_trusts = mocker.patch(
            "modules.aws_iam_role.aws_iam_role.AwsIamRoleProcessor.handle_k8s_trusts"
        )
        with pytest.raises(UserErrors):
            AwsIamRoleProcessor(app_module, layer).process(8)
        mocked_handle_iam_policy.assert_called_once_with(8)
        mocked_handle_k8s_trusts.assert_called_once_with(8)

    def test_handle_k8s_trusts(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        app_module = layer.get_module("deployerrole", 8)
        processor = AwsIamRoleProcessor(app_module, layer)
        processor.handle_k8s_trusts(module_idx=8)
        assert processor.module.data["kubernetes_trusts"] == [
            {
                "open_id_url": "${{data.terraform_remote_state.parent.outputs.k8s_openid_provider_url}}",
                "open_id_arn": "${{data.terraform_remote_state.parent.outputs.k8s_openid_provider_arn}}",
                "service_name": "*",
                "namespace": "*",
            }
        ]

    def test_handle_iam_policy(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        app_module = layer.get_module("deployerrole", 10)
        processor = AwsIamRoleProcessor(app_module, layer)
        processor.handle_iam_policy(module_idx=10)
        assert processor.module.data["iam_policy"]["Statement"] == [
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
            {
                "Action": [
                    "sqs:SendMessage",
                    "sqs:SendMessageBatch",
                    "sqs:GetQueueUrl",
                    "sqs:GetQueueAttributes",
                    "sqs:DeleteMessageBatch",
                    "sqs:DeleteMessage",
                ],
                "Effect": "Allow",
                "Resource": ["${{module.queue.queue_arn}}"],
                "Sid": "PublishQueues",
            },
            {
                "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:GetQueueUrl",
                    "sqs:GetQueueAttributes",
                ],
                "Effect": "Allow",
                "Resource": ["${{module.queue.queue_arn}}"],
                "Sid": "SubscribeQueues",
            },
            {
                "Action": ["sns:Publish"],
                "Effect": "Allow",
                "Resource": ["${{module.topic.topic_arn}}"],
                "Sid": "PublishSns",
            },
            {
                "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
                "Effect": "Allow",
                "Resource": ["${{module.queue.kms_arn}}", "${{module.topic.kms_arn}}"],
                "Sid": "KMSWrite",
            },
            {
                "Action": ["kms:Decrypt"],
                "Effect": "Allow",
                "Resource": ["${{module.queue.kms_arn}}"],
                "Sid": "KMSRead",
            },
        ]
