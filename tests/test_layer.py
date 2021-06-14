# type: ignore

import os

from pytest_mock import MockFixture

from opta.layer import Layer


class TestLayer:
    def test_parent(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "tests",
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        mocked_datadog_processor = mocker.patch("opta.layer.DatadogProcessor")
        mocked_k8s_base_processor = mocker.patch("opta.layer.AwsK8sBaseProcessor")
        mocked_eks_processor = mocker.patch("opta.layer.AwsEksProcessor")
        mocked_dns_processor = mocker.patch("opta.layer.AwsDnsProcessor")
        mocked_runx_processor = mocker.patch("opta.layer.RunxProcessor")
        mocked_aws_email_processor = mocker.patch("opta.layer.AwsEmailProcessor")
        mocked_base_processor = mocker.patch("opta.layer.ModuleProcessor")

        assert layer.name == "dummy-parent"
        assert layer.parent is None
        assert layer == layer.root()
        assert len(layer.modules) == 7
        assert layer.pre_hook(6) is None
        assert layer.post_hook(6, None) is None
        mocked_datadog_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_k8s_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_eks_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_dns_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_runx_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_aws_email_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )
        mocked_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(6),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(6, None),
            ]
        )

    def test_child(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "tests",
                "module_processors",
                "dummy_config1.yaml",
            ),
            "dummy-env",
        )
        mocked_k8s_service_processor = mocker.patch("opta.layer.AwsK8sServiceProcessor")
        mocked_base_processor = mocker.patch("opta.layer.ModuleProcessor")
        mocked_aws_iam_role_processor = mocker.patch("opta.layer.AwsIamRoleProcessor")
        mocked_aws_iam_user_processor = mocker.patch("opta.layer.AwsIamUserProcessor")
        mocked_aws_sns_processor = mocker.patch("opta.layer.AwsSnsProcessor")
        mocked_aws_sqs_processor = mocker.patch("opta.layer.AwsSqsProcessor")
        mocked_runx_processor = mocker.patch("opta.layer.RunxProcessor")

        assert layer.name == "dummy-config-1"
        assert layer.parent is not None
        assert layer.parent == layer.root()
        assert len(layer.modules) == 14
        assert layer.pre_hook(13) is None
        assert layer.post_hook(13, None) is None

        mocked_k8s_service_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_base_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_iam_role_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_iam_user_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_sns_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_aws_sqs_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
        mocked_runx_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
            ]
        )
