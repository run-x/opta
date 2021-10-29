import copy
import os
from typing import Any, Dict, List, Optional, Type

import pytest
from dns.resolver import NoNameservers
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module_processors.base import (
    DNSModuleProcessor,
    K8sBaseModuleProcessor,
    K8sServiceModuleProcessor,
)


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


class TestK8sBaseModuleProcessor:
    @staticmethod
    def process_nginx_extra_ports(
        processor: K8sBaseModuleProcessor,
        extra_ports: List[int],
        service_ports: Dict[int, str],
    ) -> Dict[int, str]:

        # mypy cannot see the mangled method, so we need to ignore type errors here
        return processor._K8sBaseModuleProcessor__process_nginx_extra_ports(extra_ports, service_ports)  # type: ignore

    def test_process_nginx_extra_ports_empty(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = []
        service_ports: Dict[int, str] = {}
        expected: Dict[int, str] = {}

        actual = self.process_nginx_extra_ports(processor, extra_ports, service_ports)

        assert actual == expected

    def test_process_nginx_extra_ports_no_service(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = [
            1,
            2,
        ]
        service_ports: Dict[int, str] = {}
        expected: Dict[int, str] = {
            1: "noservice/configured:9",
            2: "noservice/configured:9",
        }

        actual = self.process_nginx_extra_ports(processor, extra_ports, service_ports)

        assert actual == expected

    def test_process_nginx_extra_ports_with_service(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = [
            1,
            2,
        ]
        service_ports: Dict[int, str] = {
            1: "foo/bar:spam",
            3: "notin/extra:ports",
        }

        expected: Dict[int, str] = {
            1: "foo/bar:spam",
            2: "noservice/configured:9",
        }

        actual = self.process_nginx_extra_ports(processor, extra_ports, service_ports)

        assert actual == expected


class TestK8sServiceModuleProcessor:
    @pytest.fixture
    def processor(self) -> K8sServiceModuleProcessor:
        # TODO: Actually create module and layer; these tests don't depend on those
        processor = K8sServiceModuleProcessor(None, None)  # type: ignore
        processor.FLAG_MULTIPLE_PORTS_SUPPORTED = True

        return processor

    @staticmethod
    def transform_port(
        processor: K8sServiceModuleProcessor, data: Dict[Any, Any]
    ) -> None:
        # mypy cannot see the mangled method, so we need to ignore type errors here
        processor._K8sServiceModuleProcessor__transform_port(data)  # type: ignore

    def transform_port_assert(
        self,
        processor: K8sServiceModuleProcessor,
        data: Dict[Any, Any],
        *,
        expected: Optional[Dict[Any, Any]] = None,
        exception_type: Optional[Type[Exception]] = None,
        exception_message: Optional[str] = None,
    ) -> None:

        if expected is None:
            expected = copy.copy(data)

        if exception_type:
            with pytest.raises(exception_type) as e:
                self.transform_port(processor, data)

            if exception_message is not None:
                assert str(e.value) == exception_message
        else:
            self.transform_port(processor, data)

        assert data == expected

    def test_transform_port_no_port(self, processor: K8sServiceModuleProcessor) -> None:
        data = {
            "ports": "foobar",
        }
        self.transform_port_assert(processor, data)

    def test_transform_port_both(self, processor: K8sServiceModuleProcessor) -> None:
        data = {
            "port": "foo",
            "ports": "bar",
        }
        self.transform_port_assert(
            processor,
            data,
            exception_type=UserErrors,
            exception_message="Cannot specify both port and ports",
        )

    def test_transform_port_multiple_keys(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        data = {
            "port": {"foo": 1, "bar": 2},
        }
        self.transform_port_assert(
            processor,
            data,
            exception_type=UserErrors,
            exception_message="Cannot specify multiple keys in port",
        )

    def test_transform_port_unknown_type(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        data = {
            "port": {"foo": 1},
        }
        # TODO: Should this raise a different exception? Probably
        self.transform_port_assert(
            processor, data, exception_type=KeyError,
        )

    def test_transform_port_tcp(self, processor: K8sServiceModuleProcessor) -> None:
        data = {
            "port": {"tcp": 1234},
        }
        expected = {
            "ports": [{"name": "main", "type": "tcp", "port": 1234}],
        }
        self.transform_port_assert(
            processor, data, expected=expected,
        )

    def test_transform_port_grpc(self, processor: K8sServiceModuleProcessor) -> None:
        data = {
            "port": {"grpc": 5678},
        }
        expected = {
            "ports": [
                {"name": "main", "type": "http", "port": 5678, "protocol": "grpc"},
            ],
        }

        self.transform_port_assert(
            processor, data, expected=expected,
        )

    # TODO: Test __validate_ports, __read_ports, and _process_ports (split up latter)
