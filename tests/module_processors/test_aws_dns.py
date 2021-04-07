# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from opta.layer import Layer
from opta.module_processors.aws_dns import (
    CERTIFICATE_BODY_FILE_NAME,
    CERTIFICATE_CHAIN_FILE_NAME,
    PRIVATE_KEY_FILE_NAME,
    AwsDnsProcessor,
)


class TestAwsDnsProcessor:
    def test_fetch_private_key(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("opta.module_processors.aws_dns.prompt")
        patched_prompt.side_effect = [
            "",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "nonexistent_file",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_cert.pem",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_key.pem",
            ),
        ]
        AwsDnsProcessor(dns_module, layer).fetch_private_key()

    def test_fetch_cert_body(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("opta.module_processors.aws_dns.prompt")
        patched_prompt.side_effect = [
            "",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "nonexistent_file",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_cert.pem",
            ),
        ]
        AwsDnsProcessor(dns_module, layer).fetch_cert_body()

    def test_fetch_cert_chain(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("aws-dns", 6)
        patched_prompt = mocker.patch("opta.module_processors.aws_dns.prompt")
        patched_prompt.side_effect = [
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1_parent.yaml",
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "nonexistent_file",
            ),
            "",
        ]
        assert AwsDnsProcessor(dns_module, layer).fetch_cert_chain() == (None, None)

    def test_process_preexisting(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        body_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "module_processors",
            "dummy_cert.pem",
        )
        mocked_ssm = mocker.Mock()
        mocked_boto3 = mocker.patch("opta.module_processors.aws_dns.boto3")
        mocked_boto3.client.return_value = mocked_ssm
        mocked_ssm.get_parameters_by_path.return_value = {
            "Parameters": [
                {"Name": f"/opta-{layer.get_env()}/{PRIVATE_KEY_FILE_NAME}"},
                {"Name": f"/opta-{layer.get_env()}/{CERTIFICATE_BODY_FILE_NAME}"},
            ]
        }
        processor = AwsDnsProcessor(dns_module, layer)
        processor.process(2)
        mocked_boto3.client.assert_called_once_with("ssm", config=mocker.ANY)
