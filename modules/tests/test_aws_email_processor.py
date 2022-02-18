# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from modules.aws_ses.aws_ses import AwsEmailProcessor
from opta.exceptions import UserErrors
from opta.layer import Layer


class TestAwsEmailProcessor:
    def test_process(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_email_module = layer.get_module("awsses", 8)
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        with pytest.raises(UserErrors):
            AwsEmailProcessor(aws_email_module, layer).process(8)
        aws_dns_modules = layer.get_module("awsdns", 8)
        aws_dns_modules.data["delegated"] = True
        AwsEmailProcessor(aws_email_module, layer).process(8)
        assert aws_email_module.data["domain"] == "${{module.awsdns.domain}}"
        assert aws_email_module.data["zone_id"] == "${{module.awsdns.zone_id}}"

    def test_post_hook_production_enabled(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_email_module = layer.get_module("awsses", 8)

        mocked_sesv2 = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_ses.aws_ses.boto3")
        mocked_boto3.client.return_value = mocked_sesv2
        mocked_sesv2.get_account.return_value = {"ProductionAccessEnabled": True}
        aws_dns_modules = layer.get_module("awsdns", 8)
        aws_dns_modules.data["delegated"] = True
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        AwsEmailProcessor(aws_email_module, layer).post_hook(8, None)
        mocked_boto3.client.assert_called_once()
        mocked_sesv2.get_account.assert_called_once()

    def test_post_hook_pending(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_email_module = layer.get_module("awsses", 8)

        patched_logger = mocker.patch("modules.aws_ses.aws_ses.logger")
        mocked_sesv2 = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_ses.aws_ses.boto3")
        mocked_boto3.client.return_value = mocked_sesv2
        mocked_sesv2.get_account.return_value = {
            "ProductionAccessEnabled": False,
            "Details": {"ReviewDetails": {"Status": "PENDING", "CaseId": "123"}},
        }
        aws_dns_modules = layer.get_module("awsdns", 8)
        aws_dns_modules.data["delegated"] = True
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        AwsEmailProcessor(aws_email_module, layer).post_hook(8, None)
        mocked_boto3.client.assert_called_once()
        mocked_sesv2.get_account.assert_called_once()
        patched_logger.info.assert_has_calls([mocker.call(mocker.ANY)])
        patched_logger.warning.assert_not_called()

    def test_post_hook_error(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_email_module = layer.get_module("awsses", 8)

        patched_logger = mocker.patch("modules.aws_ses.aws_ses.logger")
        mocked_sesv2 = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_ses.aws_ses.boto3")
        mocked_boto3.client.return_value = mocked_sesv2
        mocked_sesv2.get_account.return_value = {
            "ProductionAccessEnabled": False,
            "Details": {"ReviewDetails": {"Status": "FAILED", "CaseId": "123"}},
        }
        aws_dns_modules = layer.get_module("awsdns", 8)
        aws_dns_modules.data["delegated"] = True
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        AwsEmailProcessor(aws_email_module, layer).post_hook(8, None)
        mocked_boto3.client.assert_called_once()
        mocked_sesv2.get_account.assert_called_once()
        patched_logger.warning.assert_has_calls([mocker.call(mocker.ANY)])
        patched_logger.info.assert_not_called()

    def test_post_hook_prompt(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config_parent.yaml"
            ),
            None,
        )
        aws_email_module = layer.get_module("awsses", 8)

        patched_prompt = mocker.patch("modules.aws_ses.aws_ses.prompt")
        patched_prompt.side_effect = ["www.blah.com", "hello, world", "blah@runx.dev"]
        patched_logger = mocker.patch("modules.aws_ses.aws_ses.logger")
        mocked_sesv2 = mocker.Mock()
        mocked_boto3 = mocker.patch("modules.aws_ses.aws_ses.boto3")
        mocked_boto3.client.return_value = mocked_sesv2
        mocked_sesv2.get_account.return_value = {
            "ProductionAccessEnabled": False,
        }
        mocked_state_storage = mocker.patch("opta.layer.Layer.state_storage")
        mocked_state_storage.return_value = "whatever"
        aws_dns_modules = layer.get_module("awsdns", 8)
        aws_dns_modules.data["delegated"] = True
        AwsEmailProcessor(aws_email_module, layer).post_hook(8, None)
        mocked_boto3.client.assert_called_once()
        mocked_sesv2.get_account.assert_called_once()
        mocked_sesv2.put_account_details.assert_called_once_with(
            MailType="TRANSACTIONAL",
            WebsiteURL="https://www.blah.com",
            ContactLanguage="EN",
            UseCaseDescription="hello, world",
            AdditionalContactEmailAddresses=["blah@runx.dev"],
            ProductionAccessEnabled=True,
        )
        patched_logger.info.assert_has_calls(
            [mocker.call(mocker.ANY), mocker.call(mocker.ANY)]
        )
        patched_logger.warning.assert_not_called()
