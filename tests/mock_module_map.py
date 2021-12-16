from modules.base import ModuleProcessor
import pytest
from pytest_mock import MockFixture as mocker
from opta.layer import Layer
def get_processor_class(module_type: str) -> ModuleProcessor:
    try:
        mock_dict = {}
        mocked_datadog_processor = mocker.patch("opta.layer.DatadogProcessor")
        mock_dict["datadog"] = mocked_datadog_processor
        mocked_k8s_base_processor = mocker.patch("opta.layer.AwsK8sBaseProcessor")
        mock_dict["aws-k8s-base"] = mocked_k8s_base_processor
        mocked_eks_processor = mocker.patch("opta.layer.AwsEksProcessor")
        mock_dict["aws-eks"] = mocked_eks_processor
        mocked_dns_processor = mocker.patch("opta.layer.AwsDnsProcessor")
        mock_dict["aws-dns"] = mocked_dns_processor
        mocked_runx_processor = mocker.patch("opta.layer.RunxProcessor")
        mock_dict["runx"] = mocked_runx_processor
        mocked_aws_email_processor = mocker.patch("opta.layer.AwsEmailProcessor")
        mock_dict["aws-ses"] = mocked_aws_email_processor
        mocked_aws_documentdb_processor = mocker.patch(
            "opta.layer.AwsDocumentDbProcessor"
        )

        mock_dict["aws-documentdb"] = mocked_aws_documentdb_processor
    except ModuleNotFoundError:
        return mocker.patch("opta.layer.ModuleProcessor")

        return mock_dict[module_type]