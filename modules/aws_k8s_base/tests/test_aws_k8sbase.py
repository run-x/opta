# type: ignore
import os

from pytest_mock import MockFixture

from modules.aws_k8s_base.aws_k8s_base import AwsK8sBaseProcessor
from opta.layer import Layer


class TestAwsK8sBaseProcessor:
    def test_add_admin_roles(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        k8s_base_module = layer.get_module("k8sbase", 8)
        k8s_base_module.data["admin_arns"] = [
            "arn:aws:iam::445935066876:user/live-example-dev-live-example-dev-deployeruser",
            "arn:aws:iam::445935066876:role/live-example-dev-live-example-dev-deployerrole",
            "arn:aws:iam::445935066876:role/silly-role",
            "arn:aws:iam::445935066876:user/silly-user",
        ]

        mocker.patch("modules.aws_k8s_base.aws_k8s_base.set_kube_config")
        mocker.patch("modules.aws_k8s_base.aws_k8s_base.load_opta_kube_config")

        mocked_core_v1_api = mocker.Mock()
        mocker.patch(
            "modules.aws_k8s_base.aws_k8s_base.CoreV1Api",
            return_value=mocked_core_v1_api,
        )
        mocked_aws_auth_config_map = mocker.Mock()
        mocked_aws_auth_config_map.data = {
            "mapRoles": "- groups: ['system:bootstrappers', 'system:nodes']\n  rolearn: arn:aws:iam::445935066876:role/opta-live-example-dev-eks-default-node-group\n  username: system:node:{{EC2PrivateDNSName}}\n- groups: ['system:masters']\n  rolearn: arn:aws:iam::445935066876:role/live-example-dev-live-example-dev-deployerrole\n  username: opta-managed\n",
            "mapUsers": "- groups: ['system:masters']\n  userarn: arn:aws:iam::445935066876:user/live-example-dev-live-example-dev-deployeruser\n  username: opta-managed\n",
        }
        mocked_opta_arns_config_map = mocker.Mock()
        mocked_opta_arns_config_map.data = {
            "adminArns": '\n- "arn:aws:iam::445935066876:user/live-example-dev-live-example-dev-deployeruser"\n\n- "arn:aws:iam::445935066876:role/live-example-dev-live-example-dev-deployerrole"\n\n- "arn:aws:iam::445935066876:role/silly-role"\n\n- "arn:aws:iam::445935066876:user/silly-user"\n'
        }
        mocked_core_v1_api.read_namespaced_config_map.side_effect = [
            mocked_aws_auth_config_map,
            mocked_opta_arns_config_map,
        ]
        AwsK8sBaseProcessor(k8s_base_module, layer).add_admin_roles()
        mocked_core_v1_api.read_namespaced_config_map.assert_has_calls(
            [mocker.call("aws-auth", "kube-system"), mocker.call("opta-arns", "default")]
        )
        mocked_core_v1_api.replace_namespaced_config_map.assert_has_calls(
            [mocker.call("aws-auth", "kube-system", body=mocked_aws_auth_config_map)]
        )

        assert mocked_aws_auth_config_map.data == {
            "mapRoles": "- groups: ['system:bootstrappers', 'system:nodes']\n  rolearn: arn:aws:iam::445935066876:role/opta-live-example-dev-eks-default-node-group\n  username: system:node:{{EC2PrivateDNSName}}\n- groups: ['system:masters']\n  rolearn: arn:aws:iam::445935066876:role/live-example-dev-live-example-dev-deployerrole\n  username: opta-managed\n- groups: ['system:masters']\n  rolearn: arn:aws:iam::445935066876:role/silly-role\n  username: opta-managed\n",
            "mapUsers": "- groups: ['system:masters']\n  userarn: arn:aws:iam::445935066876:user/live-example-dev-live-example-dev-deployeruser\n  username: opta-managed\n- groups: ['system:masters']\n  userarn: arn:aws:iam::445935066876:user/silly-user\n  username: opta-managed\n",
        }
