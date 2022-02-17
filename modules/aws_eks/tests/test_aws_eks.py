# type: ignore
import os

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
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        AwsEksProcessor(aws_eks_module, layer).post_hook(8, None)

        mocked_boto3.client.assert_called_once_with("autoscaling", config=mocker.ANY)
        mocked_autoscaling_client.describe_auto_scaling_groups.assert_called_once_with()
        mocked_autoscaling_client.enable_metrics_collection.assert_called_once_with(
            AutoScalingGroupName="dummy_name", Granularity="1Minute"
        )

    def test_process(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_eks_module = layer.get_module("awseks", 8)
        AwsEksProcessor(aws_eks_module, layer).process(8)
        assert (
            aws_eks_module.data["private_subnet_ids"]
            == "${{module.awsbase.private_subnet_ids}}"
        )
        assert (
            aws_eks_module.data["kms_account_key_arn"]
            == "${{module.awsbase.kms_account_key_arn}}"
        )
