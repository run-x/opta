import copy
import os
from typing import Any, Dict, List, Optional, Tuple, Type

import pytest
from dns.resolver import NoNameservers
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.module_processors.base import (
    DNSModuleProcessor,
    K8sBaseModuleProcessor,
    K8sServiceModuleProcessor,
    PortSpec,
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
        extra_tls_ports: List[int],
        service_ports: Dict[int, str],
    ) -> Dict[int, str]:

        # mypy cannot see the mangled method, so we need to ignore type errors here
        return processor._K8sBaseModuleProcessor__process_nginx_extra_ports(extra_ports, extra_tls_ports, service_ports)  # type: ignore

    def test_process_nginx_extra_ports_empty(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = []
        extra_tls_ports: List[int] = []
        service_ports: Dict[int, str] = {}
        expected: Dict[int, str] = {}

        actual = self.process_nginx_extra_ports(
            processor, extra_ports, extra_tls_ports, service_ports
        )

        assert actual == expected

    def test_process_nginx_extra_ports_no_service(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = [
            1,
            2,
        ]
        extra_tls_ports: List[int] = []
        service_ports: Dict[int, str] = {}
        expected: Dict[int, str] = {
            1: "noservice/configured:9",
            2: "noservice/configured:9",
        }

        actual = self.process_nginx_extra_ports(
            processor, extra_ports, extra_tls_ports, service_ports
        )

        assert actual == expected

    def test_process_nginx_extra_ports_with_service(self) -> None:
        processor = K8sBaseModuleProcessor()

        extra_ports: List[int] = [
            1,
            2,
        ]
        extra_tls_ports: List[int] = []
        service_ports: Dict[int, str] = {
            1: "foo/bar:spam",
            3: "notin/extra:ports",
        }

        expected: Dict[int, str] = {
            1: "foo/bar:spam",
            2: "noservice/configured:9",
        }

        actual = self.process_nginx_extra_ports(
            processor, extra_ports, extra_tls_ports, service_ports
        )

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

    @staticmethod
    def validate_ports(
        processor: K8sServiceModuleProcessor, ports: List[PortSpec]
    ) -> None:
        processor._K8sServiceModuleProcessor__validate_ports(ports)  # type: ignore

    def validate_ports_assert(
        self,
        processor: K8sServiceModuleProcessor,
        ports: List[PortSpec],
        *,
        exception_type: Optional[Type[Exception]] = None,
        exception_message: Optional[str] = None,
    ) -> None:

        if exception_type:
            with pytest.raises(exception_type) as e:
                self.validate_ports(processor, ports)

            if exception_message is not None:
                assert str(e.value) == exception_message
        else:
            self.validate_ports(processor, ports)

    def test_validate_ports_flag_disabled_multiple(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        processor.FLAG_MULTIPLE_PORTS_SUPPORTED = False

        ports = [
            PortSpec("a", "http", 1),
            PortSpec("b", "http", 2),
        ]

        self.validate_ports_assert(
            processor,
            ports,
            exception_type=UserErrors,
            exception_message="Cannot specify multiple ports in this cloud",
        )

    def test_validate_ports_flag_disabled_tcp(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        processor.FLAG_MULTIPLE_PORTS_SUPPORTED = False

        ports = [
            PortSpec("a", "tcp", 1),
        ]

        self.validate_ports_assert(
            processor,
            ports,
            exception_type=UserErrors,
            exception_message="Cannot specify TCP ports in this cloud",
        )

    def test_validate_ports_multiple_http(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        ports = [
            PortSpec("a", "http", 1),
            PortSpec("b", "http", 2),
        ]

        self.validate_ports_assert(
            processor,
            ports,
            exception_type=UserErrors,
            exception_message="Multiple `type: http` ports not supported",
        )

    def test_validate_ports_duplicate_name(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        ports = [
            PortSpec("a", "http", 1),
            PortSpec("a", "tcp", 2),
        ]

        self.validate_ports_assert(
            processor,
            ports,
            exception_type=UserErrors,
            exception_message="Duplicate port name `a`",
        )

    def test_validate_ports_duplicate_num(
        self, processor: K8sServiceModuleProcessor
    ) -> None:
        ports = [
            PortSpec("a", "http", 1),
            PortSpec("b", "tcp", 1),
        ]

        self.validate_ports_assert(
            processor,
            ports,
            exception_type=UserErrors,
            exception_message="Duplicate port number `1`",
        )

    @staticmethod
    def read_ports(
        processor: K8sServiceModuleProcessor, raw: List[Dict[str, Any]]
    ) -> List[PortSpec]:
        return processor._K8sServiceModuleProcessor__read_ports(raw)  # type: ignore

    def read_ports_assert(
        self,
        processor: K8sServiceModuleProcessor,
        raw: List[Dict[str, Any]],
        *,
        expected: Optional[List[PortSpec]] = None,
        exception_type: Optional[Type[Exception]] = None,
        exception_message: Optional[str] = None,
    ) -> None:

        if exception_type:
            with pytest.raises(exception_type) as e:
                self.read_ports(processor, raw)

            if exception_message is not None:
                assert str(e.value) == exception_message
        else:
            ports = self.read_ports(processor, raw)

            assert ports == expected

    # TODO: Test _process_ports (split it up first)

    def test_read_ports_empty(self, processor: K8sServiceModuleProcessor) -> None:
        self.read_ports_assert(processor, [], expected=[])

    def test_read_ports(self, processor: K8sServiceModuleProcessor) -> None:
        raw = [{"name": "a", "port": 1, "type": "http"}]

        expected = [
            PortSpec("a", "http", 1),
        ]

        self.read_ports_assert(processor, raw, expected=expected)


class TestPortSpec:
    def from_raw_assert(
        self,
        raw: Dict[str, Any],
        *,
        expected: Optional[PortSpec] = None,
        exception_type: Optional[Type[Exception]] = None,
        exception_message: Optional[str] = None,
    ) -> None:

        if exception_type:
            with pytest.raises(exception_type) as e:
                PortSpec.from_raw(raw)

            if exception_message is not None:
                assert str(e.value) == exception_message
        else:
            actual = PortSpec.from_raw(raw)

            assert actual == expected

    def test_from_raw_simple(self) -> None:
        self.from_raw_assert(
            {"name": "a", "type": "http", "port": 1},
            expected=PortSpec("a", "http", 1, None, False),
        )

    def test_from_raw_advanced(self) -> None:
        self.from_raw_assert(
            {"name": "a", "type": "http", "port": 1, "protocol": "grpc", "tls": True},
            expected=PortSpec("a", "http", 1, "grpc", True),
        )

    def test_from_raw_invalid_type(self) -> None:
        self.from_raw_assert(
            {"name": "a", "type": "foo", "port": 1},
            exception_type=ValueError,
            exception_message="Invalid type/protocol combo: foo/None",
        )

    def test_from_raw_invalid_protocol(self) -> None:
        self.from_raw_assert(
            {"name": "a", "type": "http", "port": 1, "protocol": "bar"},
            exception_type=ValueError,
            exception_message="Invalid type/protocol combo: http/bar",
        )

    def test_valid_type_protocols(self) -> None:
        protos = PortSpec.valid_type_protocols()

        assert len(protos) > 0

        for type, protocol in protos:
            assert len(type) > 0
            if protocol:
                assert len(protocol) > 0

    def test_is_http(self) -> None:
        assert PortSpec("a", "http", 1).is_http is True
        assert PortSpec("a", "tcp", 1).is_http is False

    def test_is_tcp(self) -> None:
        assert PortSpec("a", "http", 1).is_tcp is False
        assert PortSpec("a", "tcp", 1).is_tcp is True

    def test_probe_type(self) -> None:
        tests: Dict[Tuple[str, Optional[str]], str] = {
            ("http", None): "http",
            ("http", "grpc"): "tcp",
            ("tcp", None): "tcp",
        }

        for input, expected in tests.items():
            spec = PortSpec("a", input[0], 1, input[1])
            assert spec.probe_type == expected

    def test_to_json(self) -> None:
        spec = PortSpec("a", "http", 1, "grpc", True)
        expected = {
            "name": "a",
            "type": "http",
            "port": 1,
            "protocol": "grpc",
            "tls": True,
            "probeType": "tcp",
        }

        assert spec.__to_json__() == expected
