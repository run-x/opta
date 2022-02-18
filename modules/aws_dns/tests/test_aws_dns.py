# type: ignore
import os

from pytest_mock import MockFixture

from modules.aws_dns.aws_dns import (
    CERTIFICATE_BODY_FILE_NAME,
    PRIVATE_KEY_FILE_NAME,
    AwsDnsProcessor,
)
from opta.layer import Layer


class TestAwsDnsProcessor:
    def test_fetch_private_key(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("modules.aws_dns.aws_dns.prompt")
        patched_prompt.side_effect = [
            "",
            os.path.join(
                os.getcwd(),
                "tests",
                "fixtures",
                "dummy_data",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "nonexistent_file"
            ),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_cert.pem"
            ),
            os.path.join(os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_key.pem"),
        ]
        AwsDnsProcessor(dns_module, layer).fetch_private_key()

    def test_fetch_cert_body(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("modules.aws_dns.aws_dns.prompt")
        patched_prompt.side_effect = [
            "",
            os.path.join(
                os.getcwd(),
                "tests",
                "fixtures",
                "dummy_data",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "nonexistent_file"
            ),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_cert.pem"
            ),
        ]
        AwsDnsProcessor(dns_module, layer).fetch_cert_body()

    def test_fetch_cert_chain(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("modules.aws_dns.aws_dns.prompt")
        patched_prompt.side_effect = [
            os.path.join(
                os.getcwd(),
                "tests",
                "fixtures",
                "dummy_data",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "nonexistent_file"
            ),
            "",
        ]
        assert AwsDnsProcessor(dns_module, layer).fetch_cert_chain() == (None, None)

    def test_process_preexisting(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        mocked_ssm = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_dns.aws_dns.boto3")
        mocked_boto3.client.return_value = mocked_ssm
        mocked_ssm.get_parameters_by_path.return_value = {
            "Parameters": [
                {"Name": f"/opta-{layer.get_env()}/{PRIVATE_KEY_FILE_NAME}"},
                {"Name": f"/opta-{layer.get_env()}/{CERTIFICATE_BODY_FILE_NAME}"},
            ]
        }
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        processor = AwsDnsProcessor(dns_module, layer)
        processor.process(2)
        mocked_boto3.client.assert_called_once_with("ssm", config=mocker.ANY)

    def test_process_new(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        mocked_ssm = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_dns.aws_dns.boto3")
        mocked_boto3.client.return_value = mocked_ssm
        mocked_ssm.get_parameters_by_path.return_value = {"Parameters": []}

        patched_prompt = mocker.patch("modules.aws_dns.aws_dns.prompt")
        patched_prompt.side_effect = [
            os.path.join(os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_key.pem"),
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_cert.pem"
            ),
            "",
        ]
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        processor = AwsDnsProcessor(dns_module, layer)
        processor.process(2)
        mocked_boto3.client.assert_called_once_with("ssm", config=mocker.ANY)
        mocked_ssm.put_parameter.assert_has_calls(
            [
                mocker.call(
                    Name=mocker.ANY,
                    Value=mocker.ANY,
                    Type="SecureString",
                    Overwrite=True,
                ),
                mocker.call(
                    Name=mocker.ANY,
                    Value=mocker.ANY,
                    Type="SecureString",
                    Overwrite=True,
                ),
            ]
        )

    def test_process_new_external(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        del dns_module.data["upload_cert"]
        dns_module.data["external_cert_arn"] = "blah"
        mocked_acm = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_dns.aws_dns.boto3")
        mocked_boto3.client.return_value = mocked_acm
        mocked_acm.describe_certificate.return_value = {
            "Certificate": {"DomainName": "www.blah.com", "SubjectAlternativeNames": []}
        }
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        processor = AwsDnsProcessor(dns_module, layer)
        processor.process(2)
        mocked_boto3.client.assert_called_once_with("acm", config=mocker.ANY)
        mocked_acm.describe_certificate.assert_called_once_with(CertificateArn="blah")
