import os

import pytest
from dns.resolver import NoNameservers
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module_processors.base import DNSModuleProcessor


class TestBaseModuleProcessors:
    def test_validate_dns_delegated_false(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )

        dns_module = layer.get_module("awsdns", 6)
        if dns_module is None:
            raise Exception("did not find dns module")
        del dns_module.data["upload_cert"]
        dns_module.data["delegated"] = False
        mocked_get_terraform_outputs = mocker.patch(
            "opta.module_processors.base.get_terraform_outputs"
        )
        processor = DNSModuleProcessor(dns_module, layer)
        processor.validate_dns()
        mocked_get_terraform_outputs.assert_not_called()

    def test_validate_dns_no_outputs(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        if dns_module is None:
            raise Exception("did not find dns module")
        del dns_module.data["upload_cert"]
        dns_module.data["delegated"] = True
        mocked_get_terraform_outputs = mocker.patch(
            "opta.module_processors.base.get_terraform_outputs"
        )
        mocked_get_terraform_outputs.return_value = {}
        processor = DNSModuleProcessor(dns_module, layer)
        with pytest.raises(UserErrors):
            processor.validate_dns()
        mocked_get_terraform_outputs.assert_called_once()

    def test_validate_dns_no_name_servers(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        if dns_module is None:
            raise Exception("did not find dns module")
        del dns_module.data["upload_cert"]
        dns_module.data["delegated"] = True
        processor = DNSModuleProcessor(dns_module, layer)
        mocked_get_terraform_outputs = mocker.patch(
            "opta.module_processors.base.get_terraform_outputs"
        )
        mocked_get_terraform_outputs.return_value = {
            "name_servers": ["blah.com", "baloney.com"]
        }
        mocked_query = mocker.patch("opta.module_processors.base.query")
        mocked_query.side_effect = NoNameservers("No name servers found")  # type: ignore
        with pytest.raises(UserErrors):
            processor.validate_dns()
        mocked_query.assert_called_once()

    def test_validate_dns_mismatch(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        if dns_module is None:
            raise Exception("did not find dns module")
        del dns_module.data["upload_cert"]
        dns_module.data["delegated"] = True
        processor = DNSModuleProcessor(dns_module, layer)
        mocked_get_terraform_outputs = mocker.patch(
            "opta.module_processors.base.get_terraform_outputs"
        )
        mocked_get_terraform_outputs.return_value = {
            "name_servers": ["blah.com.", "baloney.com"]
        }
        mocked_query = mocker.patch("opta.module_processors.base.query")
        mocked_1 = mocker.Mock()
        mocked_1.target = mocker.Mock()
        mocked_1.target.to_text.return_value = "baloney.com"
        mocked_2 = mocker.Mock()
        mocked_2.target = mocker.Mock()
        mocked_2.target.to_text.return_value = "bla.com"
        mocked_query.return_value = [mocked_1, mocked_2]
        with pytest.raises(UserErrors):
            processor.validate_dns()

    def test_validate_all_good(self, mocker: MockFixture) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config_parent.yaml",
            ),
            None,
        )
        dns_module = layer.get_module("awsdns", 6)
        if dns_module is None:
            raise Exception("did not find dns module")
        del dns_module.data["upload_cert"]
        dns_module.data["delegated"] = True
        processor = DNSModuleProcessor(dns_module, layer)
        mocked_get_terraform_outputs = mocker.patch(
            "opta.module_processors.base.get_terraform_outputs"
        )
        mocked_get_terraform_outputs.return_value = {
            "name_servers": ["blah.com.", "baloney.com"]
        }
        mocked_query = mocker.patch("opta.module_processors.base.query")
        mocked_1 = mocker.Mock()
        mocked_1.target = mocker.Mock()
        mocked_1.target.to_text.return_value = "baloney.com"
        mocked_2 = mocker.Mock()
        mocked_2.target = mocker.Mock()
        mocked_2.target.to_text.return_value = "blah.com"
        mocked_query.return_value = [mocked_1, mocked_2]
        processor.validate_dns()
