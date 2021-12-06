# type: ignore

import os

import pytest
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer


class TestLayer:
    def test_infinite_loop_prevention(self):
        with pytest.raises(UserErrors):
            Layer.load_from_yaml(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "infinite_loop.yaml",
                ),
                None,
            )

    def test_same_name_as_parent(self):
        with pytest.raises(UserErrors):
            Layer.load_from_yaml(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "same_name_as_parent.yaml",
                ),
                None,
            )

    def test_get_event_properties(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )

        assert layer.get_event_properties() == {
            "layer_name": "dummy-config-1",
            "module_aws_documentdb": 2,
            "module_aws_dynamodb": 1,
            "module_aws_k8s_service": 2,
            "module_aws_postgres": 2,
            "module_aws_redis": 2,
            "org_name": "opta-tests",
            "parent_name": "dummy-parent",
            "total_resources": 9,
        }

    def test_parent(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        mocked_datadog_processor = mocker.patch("opta.layer.DatadogProcessor")
        layer.PROCESSOR_DICT["datadog"] = mocked_datadog_processor
        mocked_k8s_base_processor = mocker.patch("opta.layer.AwsK8sBaseProcessor")
        layer.PROCESSOR_DICT["aws-k8s-base"] = mocked_k8s_base_processor
        mocked_eks_processor = mocker.patch("opta.layer.AwsEksProcessor")
        layer.PROCESSOR_DICT["aws-eks"] = mocked_eks_processor
        mocked_dns_processor = mocker.patch("opta.layer.AwsDnsProcessor")
        layer.PROCESSOR_DICT["aws-dns"] = mocked_dns_processor
        mocked_runx_processor = mocker.patch("opta.layer.RunxProcessor")
        layer.PROCESSOR_DICT["runx"] = mocked_runx_processor
        mocked_aws_email_processor = mocker.patch("opta.layer.AwsEmailProcessor")
        layer.PROCESSOR_DICT["aws-ses"] = mocked_aws_email_processor
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
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        mocked_k8s_service_processor = mocker.patch("opta.layer.AwsK8sServiceProcessor")
        layer.PROCESSOR_DICT["aws-k8s-service"] = mocked_k8s_service_processor
        mocked_aws_iam_role_processor = mocker.patch("opta.layer.AwsIamRoleProcessor")
        layer.PROCESSOR_DICT["aws-iam-role"] = mocked_aws_iam_role_processor
        mocked_aws_iam_user_processor = mocker.patch("opta.layer.AwsIamUserProcessor")
        layer.PROCESSOR_DICT["aws-iam-user"] = mocked_aws_iam_user_processor
        mocked_aws_sns_processor = mocker.patch("opta.layer.AwsSnsProcessor")
        layer.PROCESSOR_DICT["aws-sns"] = mocked_aws_sns_processor
        mocked_aws_sqs_processor = mocker.patch("opta.layer.AwsSqsProcessor")
        layer.PROCESSOR_DICT["aws-sqs"] = mocked_aws_sqs_processor
        mocked_runx_processor = mocker.patch("opta.layer.RunxProcessor")
        layer.PROCESSOR_DICT["runx"] = mocked_runx_processor
        mocked_aws_documentdb_processor = mocker.patch(
            "opta.layer.AwsDocumentDbProcessor"
        )
        layer.PROCESSOR_DICT["aws-documentdb"] = mocked_aws_documentdb_processor
        mocked_base_processor = mocker.patch("opta.layer.ModuleProcessor")

        assert layer.name == "dummy-config-1"
        assert layer.parent is not None
        assert layer.parent == layer.root()
        assert len(layer.modules) == 16
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

        mocked_aws_documentdb_processor.assert_has_calls(
            [
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().pre_hook(13),
                mocker.call(mocker.ANY, layer),
                mocker.call().post_hook(13, None),
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
