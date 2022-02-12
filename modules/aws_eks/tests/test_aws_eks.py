# type: ignore
import os

import boto3
from botocore.config import Config
from mypy_boto3_eks import EKSClient
from pytest_mock import MockFixture

from modules.aws_eks.aws_eks import AwsEksProcessor
from opta.layer import Layer


class TestAwsEksModuleProcessor:
    def test_cleanup_security_groups(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        mocked_ec2_client = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_eks.aws_eks.boto3")
        mocked_boto3.client.return_value = mocked_ec2_client
        mocked_ec2_client.describe_vpcs.return_value = {"Vpcs": [{"VpcId": "abc"}]}
        mocked_ec2_client.describe_security_groups.return_value = {
            "SecurityGroups": [{"GroupId": "efg"}]
        }
        AwsEksProcessor(aws_eks_module, layer).cleanup_security_groups("us-east-1")
        mocked_ec2_client.describe_vpcs.assert_called_once_with(
            Filters=[
                {"Name": "tag:layer", "Values": [layer.name]},
                {"Name": "tag:opta", "Values": ["true"]},
            ]
        )
        mocked_ec2_client.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    "Name": f"tag:kubernetes.io/cluster/opta-{layer.name}",
                    "Values": ["owned"],
                },
                {"Name": "vpc-id", "Values": ["abc"]},
            ],
        )
        mocked_ec2_client.delete_security_group.assert_called_once_with(GroupId="efg")

    def test_post_hook(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        aws_eks_module.data["enable_metrics"] = True
        mocked_autoscaling_client = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_eks.aws_eks.boto3")
        mocked_boto3.client.return_value = mocked_autoscaling_client
        cluster_name = f"opta-{layer.root().name}"

        mocked_autoscaling_client.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [
                {
                    "AutoScalingGroupName": "dummy_name",
                    "Tags": [
                        {
                            "Key": f"kubernetes.io/cluster/{cluster_name}",
                            "Value": "owned",
                        },
                        {
                            "Key": "eks:nodegroup-name",
                            "Value": f"{cluster_name}-default-897896",
                        },
                    ],
                },
                {
                    "AutoScalingGroupName": "dummy_name1",
                    "Tags": [
                        {
                            "Key": f"kubernetes.io/cluster/{cluster_name}",
                            "Value": "owned",
                        },
                        {
                            "Key": "eks:nodegroup-name",
                            "Value": f"{cluster_name}-blah-897896",
                        },
                    ],
                },
                {
                    "AutoScalingGroupName": "dummy_name2",
                    "Tags": [
                        {"Key": "kubernetes.io/cluster/silly", "Value": "owned"},
                        {
                            "Key": "eks:nodegroup-name",
                            "Value": f"{cluster_name}-default-897896",
                        },
                    ],
                },
            ]
        }

        AwsEksProcessor(aws_eks_module, layer).post_hook(8, None)

        mocked_boto3.client.assert_called_once_with("autoscaling", config=mocker.ANY)
        mocked_autoscaling_client.describe_auto_scaling_groups.assert_called_once_with()
        mocked_autoscaling_client.enable_metrics_collection.assert_called_once_with(
            AutoScalingGroupName="dummy_name", Granularity="1Minute"
        )

    def test_delete_preexisting_cloudwatch_log_group_no_cluster_name(
        self, mocker: MockFixture
    ):
        mocked_get_cluster_name = mocker.patch("modules.aws_eks.aws_eks.get_cluster_name")
        mocked_get_cluster_name.return_value = None

        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        AwsEksProcessor(aws_eks_module, layer).delete_preexisting_cloudwatch_log_group(
            "us-east-1"
        )
        mocked_get_cluster_name.assert_called_once()

    def test_delete_preexisting_cloudwatch_log_group_cluster_found(
        self, mocker: MockFixture
    ):
        mocked_get_cluster_name = mocker.patch("modules.aws_eks.aws_eks.get_cluster_name")
        mocked_get_cluster_name.return_value = "blah"
        mocked_eks_client = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_eks.aws_eks.boto3")
        mocked_boto3.client.return_value = mocked_eks_client
        mocked_eks_client.describe_cluster.return_value = {"cluster": {}}

        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        AwsEksProcessor(aws_eks_module, layer).delete_preexisting_cloudwatch_log_group(
            "us-east-1"
        )
        mocked_boto3.client.assert_called_once()
        mocked_get_cluster_name.assert_called_once()

    def test_delete_preexisting_cloudwatch_log_group_all_the_way(
        self, mocker: MockFixture
    ):
        eks_client: EKSClient = boto3.client(
            "eks", config=Config(region_name="us-east-1")
        )
        mocked_get_cluster_name = mocker.patch("modules.aws_eks.aws_eks.get_cluster_name")
        mocked_get_cluster_name.return_value = "blah"
        mocked_eks_client = mocker.Mock()
        mocked_eks_client.exceptions = eks_client.exceptions
        mocked_cloudwatch_client = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_eks.aws_eks.boto3")
        mocked_boto3.client.side_effect = [mocked_eks_client, mocked_cloudwatch_client]
        mocked_eks_client.describe_cluster.side_effect = eks_client.exceptions.ResourceNotFoundException(
            {}, "hi"
        )
        mocked_cloudwatch_client.describe_log_groups.return_value = {"logGroups": ["a"]}

        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        AwsEksProcessor(aws_eks_module, layer).delete_preexisting_cloudwatch_log_group(
            "us-east-1"
        )
        mocked_boto3.client.assert_has_calls(
            [
                mocker.call("eks", config=mocker.ANY),
                mocker.call("logs", config=mocker.ANY),
            ]
        )
        mocked_get_cluster_name.assert_called_once()
        mocked_cloudwatch_client.delete_log_group.assert_called_once()

    def test_process(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        mocked_delete_preexisting_cloudwatch_log_group = mocker.patch(
            "modules.aws_eks.aws_eks.AwsEksProcessor.delete_preexisting_cloudwatch_log_group"
        )
        AwsEksProcessor(aws_eks_module, layer).process(8)
        assert (
            aws_eks_module.data["private_subnet_ids"]
            == "${{module.awsbase.private_subnet_ids}}"
        )
        assert (
            aws_eks_module.data["kms_account_key_arn"]
            == "${{module.awsbase.kms_account_key_arn}}"
        )
        mocked_delete_preexisting_cloudwatch_log_group.assert_called()
