import dataclasses
import math
from platform import system
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)

from dns.rdtypes.ANY.NS import NS
from dns.resolver import Answer, NoNameservers, query

from opta.constants import REGISTRY
from opta.core import kubernetes
from opta.core.aws import AWS
from opta.core.helm import Helm
from opta.core.helm_cloud_client import HelmCloudClient
from opta.core.terraform import get_terraform_outputs
from opta.exceptions import UserErrors
from opta.utils import RawString, hydrate, json, logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


NGINX_EXTRA_TCP_PORTS_ANNOTATION = "nginx.opta.dev/extra-tcp-ports"
NGINX_PLACEHOLDER_SERVICE = (
    "noservice/configured:9"  # Port 9 on TCP/UDP is the "Discard" protocol
)
NGINX_TCP_CONFIGMAP = ("ingress-nginx", "ingress-nginx-tcp")  # Namespace, name


class ModuleProcessor:
    def __init__(self, module: "Module", layer: "Layer") -> None:
        self.layer = layer
        self.module = module
        super(ModuleProcessor, self).__init__()

    def process(self, module_idx: int) -> None:
        if self.module.data.get("root_only", False) and self.layer.parent is not None:
            raise UserErrors(
                f"Module {self.module.name} can only specified in a root layer"
            )
        self.module.data["env_name"] = self.layer.get_env()
        self.module.data["layer_name"] = self.layer.name
        self.module.data["module_name"] = self.module.name

    def get_event_properties(self) -> Dict[str, int]:
        module_type = self.module.aliased_type or self.module.type
        module_instance_count = REGISTRY[self.layer.cloud]["modules"][module_type].get(
            "metric_count", 0
        )
        if module_instance_count != 0:
            return {f"module_{module_type.replace('-', '_')}": module_instance_count}
        return {}

    def pre_hook(self, module_idx: int) -> None:
        pass

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        pass

    def post_delete(self, module_idx: int) -> None:
        pass

    @property
    def required_path_dependencies(self) -> FrozenSet[str]:
        """
        Returns a frozen set of executables that are required to be on the PATH in order for this module processor to function.
        Should be extended by module processors as needed.
        """
        return frozenset()


class DNSModuleProcessor(ModuleProcessor):
    def validate_dns(self) -> None:

        if not self.module.data.get("delegated", False):
            return

        current_outputs = get_terraform_outputs(self.layer)
        if "name_servers" not in current_outputs:
            raise UserErrors(
                "Did not find name_servers field in output. Please apply one with delegated set to false. (might take some time to propagate)"
            )
        expected_name_servers: List[str] = current_outputs["name_servers"]
        expected_name_servers = [x.strip(".") for x in expected_name_servers]
        try:
            answers: Answer = query(self.module.data["domain"], "NS")  # type: ignore
        except NoNameservers:
            raise UserErrors(
                f"Did not find any NS records for domain {self.module.data['domain']}. (might take some time to propagate)"
            )
        answer: NS
        actual_name_servers = []
        for answer in answers:
            ns_server = answer.target.to_text(omit_final_dot=True)
            actual_name_servers.append(ns_server)
        if set(expected_name_servers) != set(actual_name_servers):
            raise UserErrors(
                f"Incorrect NS servers. Expected {expected_name_servers}, actual {actual_name_servers}. (might take some time to propagate)"
            )


@dataclasses.dataclass
class PortSpec:
    name: str
    type: str
    port: int
    service_port: int
    protocol: Optional[str] = None
    tls: bool = False

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "PortSpec":
        spec = cls(
            name=raw["name"],
            type=raw["type"],
            port=raw["port"],
            service_port=raw.get(
                "service_port", cls._default_service_port(raw["type"], raw["port"])
            ),
            protocol=raw.get("protocol"),
            tls=raw.get("tls", False),
        )

        if (spec.type, spec.protocol) not in cls.valid_type_protocols():
            raise ValueError(f"Invalid type/protocol combo: {spec.type}/{spec.protocol}")

        return spec

    @staticmethod
    def valid_type_protocols() -> Set[Tuple[str, Optional[str]]]:
        return {
            ("http", None),
            ("http", "grpc"),
            ("http", "websocket"),
            ("tcp", None),
        }

    @staticmethod
    def legacy_port_type_mapping() -> Dict[str, Tuple[str, Optional[str]]]:
        return {
            "http": ("http", None),
            "grpc": ("http", "grpc"),
            "websocket": ("http", "websocket"),
            "tcp": ("http", "websocket"),
        }

    @property
    def is_http(self) -> bool:
        return self.type == "http"

    @property
    def is_tcp(self) -> bool:
        return self.type == "tcp"

    @property
    def probe_type(self) -> Union[Literal["http"], Literal["tcp"]]:
        """The type of health probe to use with this port, either "tcp" or "http"."""

        if self.type == "http" and self.protocol is None:
            # Only plain HTTP can handle an HTTP probe
            return "http"

        return "tcp"

    @staticmethod
    def _default_service_port(type: str, port: int) -> int:
        if type == "http":
            return 80

        return port

    def __to_json__(self) -> Dict[str, Any]:
        values = dataclasses.asdict(self)
        values["probeType"] = self.probe_type

        values["servicePort"] = self.service_port
        del values["service_port"]

        return values


class K8sServiceModuleProcessor(ModuleProcessor):
    # TODO(patrick): Remove this flag and references to it once all clouds support multiple ports
    FLAG_MULTIPLE_PORTS_SUPPORTED = False

    def pre_hook(self, module_idx: int) -> None:
        release_name = f"{self.layer.name}-{self.module.name}"
        cloud_client = self.layer.get_cloud_client()

        # TODO(patrick): We could probably just always run this check
        # If we are running a BYOK cluster, make sure linkerd and nginx are installed.
        if isinstance(cloud_client, HelmCloudClient):
            self._check_byok_ready()

        kube_context = cloud_client.get_kube_context_name()
        pending_upgrade_helm_chart = Helm.get_helm_list(
            kube_context=kube_context, release=release_name, status="pending-upgrade"
        )
        if pending_upgrade_helm_chart:
            raise UserErrors(
                f"There is a pending upgrade for the helm chart: {release_name}."
                "\nIt will cause this command to fail. Please use `opta force-unlock` to rollback to a consistent state first."
            )
        return super().pre_hook(module_idx)

    @property
    def required_path_dependencies(self) -> FrozenSet[str]:
        return super().required_path_dependencies | kubernetes.get_required_path_executables(
            self.layer.cloud
        )

    def process(self, module_idx: int) -> None:
        # Min containers must be less than or equal to max containers and can only be 0 if both are
        min_containers_str = str(self.module.data.get("min_containers", ""))
        max_containers_str = str(self.module.data.get("max_containers", ""))
        if min_containers_str.isdigit() and max_containers_str.isdigit():
            min_containers = int(min_containers_str)
            max_containers = int(max_containers_str)
            if min_containers > max_containers:
                raise UserErrors(
                    "Min containers must be less than or equal to max containers"
                )
            if min_containers == 0 and max_containers != 0:
                raise UserErrors(
                    "Min containers can only equal 0 if max containers equals zero"
                )

        self._process_ports(self.module.data)

        if isinstance(self.module.data.get("public_uri"), str):
            self.module.data["public_uri"] = [self.module.data["public_uri"]]

        cron_jobs = self.module.data.get("cron_jobs", [])
        for cron_job in cron_jobs:
            cron_job["args"] = cron_job.get("args", [])

        if "public_uri" in self.module.data:
            new_uris: List[str] = []
            public_uri: str
            for public_uri in self.module.data["public_uri"]:
                if public_uri.startswith("/"):
                    new_uris.append(f"all{public_uri}")
                elif public_uri.startswith("*"):
                    new_uris.append(f"all{public_uri[1:]}")
                else:
                    new_uris.append(public_uri)
            self.module.data["public_uri"] = new_uris

        liveness_probe_command = self.module.data.get(
            "healthcheck_command"
        ) or self.module.data.get("liveness_probe_command")
        liveness_probe_path = self.module.data.get(
            "healthcheck_path"
        ) or self.module.data.get("liveness_probe_path")
        if liveness_probe_path is not None and liveness_probe_command is not None:
            raise UserErrors(
                "Invalid liveness probes: you can only specify a path for an http get request or a shell command to run, not both."
            )

        readiness_probe_command = self.module.data.get(
            "healthcheck_command"
        ) or self.module.data.get("readiness_probe_command")
        readiness_probe_path = self.module.data.get(
            "healthcheck_path"
        ) or self.module.data.get("readiness_probe_path")
        if readiness_probe_path is not None and readiness_probe_command is not None:
            raise UserErrors(
                "Invalid readiness probes: you can only specify a path for an http get request or a shell command to run, not both."
            )

        super(K8sServiceModuleProcessor, self).process(module_idx)

    def get_event_properties(self) -> Dict[str, int]:
        min_max_container_data = {
            "min_containers": self.module.data.get("min_containers", 1),
            "max_containers": self.module.data.get("max_containers", 3),
        }
        min_max_container_data = hydrate(
            min_max_container_data,
            {
                "vars": SimpleNamespace(**self.layer.variables),
                "variables": SimpleNamespace(**self.layer.variables),
            },
        )

        try:
            min_containers = int(min_max_container_data["min_containers"])
        except Exception:
            min_containers = 1
        try:
            max_containers = int(min_max_container_data["max_containers"])
        except Exception:
            max_containers = 3

        if self.layer.cloud == "aws":
            key = "module_aws_k8s_service"
        elif self.layer.cloud == "google":
            key = "module_gcp_k8s_service"
        elif self.layer.cloud == "azurerm":
            key = "module_azure_k8s_service"
        else:
            key = "module_local_k8s_service"
        return {key: math.ceil((min_containers + max_containers) / 2)}

    def post_delete(self, module_idx: int) -> None:
        # Helm doesn't delete PVC https://github.com/helm/helm/issues/5156
        if self.module.data.get("persistent_storage", False):
            kubernetes.delete_persistent_volume_claims(
                namespace=self.layer.name, opta_managed=True, async_req=True
            )

        super(K8sServiceModuleProcessor, self).post_delete(module_idx)

    def _check_byok_ready(self) -> None:
        errors = []
        if not self._is_linkerd_installed():
            errors.append("Linkerd2 is not installed on the cluster")

        if not self._is_nginx_ingress_installed():
            errors.append("NGINX ingress controller is not installed on the cluster")

        if not errors:
            return

        # If we have more than 2 checks, we need to make this join smarter so the message isn't "foo and bar and spam"
        msg = " and ".join(errors)

        raise UserErrors(msg)

    def _is_linkerd_installed(self) -> bool:
        # Check if linkerd namespace exists
        namespaces = kubernetes.list_namespaces()

        return any(self.__is_linkerd_ns(ns) for ns in namespaces)

    @staticmethod
    def __is_linkerd_ns(ns: kubernetes.V1Namespace) -> bool:
        meta: kubernetes.V1ObjectMeta = ns.metadata
        if not meta.labels:
            return False

        is_control_plane: str = meta.labels.get("linkerd.io/is-control-plane", "false")

        if is_control_plane.lower() != "true":
            return False

        # Fail check if the linkerd namespace is being deleted
        return ns.status.phase == "Active"

    def _is_nginx_ingress_installed(self) -> bool:
        ingress_classes = kubernetes.list_ingress_classes()

        return any(cls.metadata.name == "nginx" for cls in ingress_classes)

    def _extra_ports_controller(self) -> None:
        reconcile_nginx_extra_ports()

    def _process_ports(self, data: Dict[Any, Any]) -> None:
        self.__transform_port(data)

        if "ports" not in data:
            return

        ports = self.__read_ports(data["ports"])
        self.__validate_ports(ports)
        data["ports"] = ports

        http_port = next((port for port in ports if port.is_http), None)
        data["http_port"] = http_port

        if "probe_port" in data:
            try:
                probe_port = next(
                    port for port in ports if port.name == data["probe_port"]
                )

            except StopIteration:
                raise UserErrors(
                    f"invalid probe_port: {data['probe_port']} is not a valid port name"
                )
        else:
            probe_port = ports[0]

        data["probe_port"] = probe_port

        data["service_annotations"] = self.__service_annotations(ports)

    def __read_ports(self, raw: List[Dict[str, Any]]) -> List[PortSpec]:
        def convert(raw_spec: Dict[str, Any]) -> PortSpec:
            try:
                return PortSpec.from_raw(raw_spec)
            except ValueError as e:
                name = raw_spec.get("name", "unnamed")

                raise UserErrors(f"Issue with port {name}: {str(e)}") from e

        return [convert(raw_spec) for raw_spec in raw]

    def __service_annotations(self, ports: List[PortSpec]) -> Dict[str, str]:
        """Returns list of annotations to put on the service resources"""
        if not self.FLAG_MULTIPLE_PORTS_SUPPORTED:
            return {}

        port_mapping = {port.service_port: port.name for port in ports if port.is_tcp}

        if not port_mapping:
            return {}

        return {
            # Use RawString here to prevent the json-encoded value being "hydrated"
            # TODO FIXME(patrick): RawString is a workaround and I hate it. https://www.youtube.com/watch?v=31g0YE61PLQ
            NGINX_EXTRA_TCP_PORTS_ANNOTATION: RawString(json.dumps(port_mapping)),
        }

    def __transform_port(self, data: Dict[Any, Any]) -> None:
        if "port" not in data:
            if not self.FLAG_MULTIPLE_PORTS_SUPPORTED:
                raise UserErrors("`port` is required in the service definition")

            return

        if "ports" in data:
            raise UserErrors("Cannot specify both port and ports")

        port_type_mapping = PortSpec.legacy_port_type_mapping()

        port_config = data["port"]
        if len(port_config) > 1:
            raise UserErrors("Cannot specify multiple keys in port")

        # This will only run once, but is a clean way to get the only key,value pair
        for type, port in port_config.items():
            try:
                type_config = port_type_mapping[type]
            except KeyError:
                raise UserErrors(f"Unknown port type {type}")

            port_spec = {
                "name": "main",
                "type": type_config[0],
                "port": port,
                "service_port": 80,
            }

            if type_config[1]:
                port_spec["protocol"] = type_config[1]

            data["ports"] = [port_spec]

        del data["port"]

    def __validate_ports(self, ports: List[PortSpec]) -> None:
        if not self.FLAG_MULTIPLE_PORTS_SUPPORTED:
            if len(ports) > 1:
                raise UserErrors("Cannot specify multiple ports in this cloud")

            if len([port for port in ports if port.is_tcp]):
                raise UserErrors("Cannot specify TCP ports in this cloud")

        # Make sure we only have at most one http port
        http_ports = [port for port in ports if port.is_http]
        if len(http_ports) > 1:
            raise UserErrors("Multiple `type: http` ports not supported")

        # Check for duplicate port numbers or names
        uniques: Dict[str, Callable[[PortSpec], Any]] = {
            "port name": lambda port: port.name,
            "port number": lambda port: port.port,
            "service port number": lambda port: port.service_port,
        }

        for key, resolver in uniques.items():
            values = set()
            for port in ports:
                value = resolver(port)
                if value in values:
                    raise UserErrors(f"Duplicate {key} `{value}`")

                values.add(value)


class K8sBaseModuleProcessor:
    def _process_nginx_extra_ports(self, layer: "Layer", data: Dict[Any, Any]) -> None:
        extra_ports: List[int] = data.get("nginx_extra_tcp_ports", [])
        extra_tls_ports: List[int] = data.get("nginx_extra_tcp_ports_tls", [])

        # stateless mode - no k8s available
        if layer.is_stateless_mode() is True:
            data["nginx_extra_tcp_ports"] = {}
            return

        kubernetes.set_kube_config(layer)
        service_port_mapping = reconcile_nginx_extra_ports(update_config_map=False)

        # In a separate function to make logic more testable
        data["nginx_extra_tcp_ports"] = self.__process_nginx_extra_ports(
            extra_ports, extra_tls_ports, service_port_mapping
        )

    def __process_nginx_extra_ports(
        self,
        extra_ports: List[int],
        extra_tls_ports: List[int],
        service_ports: Dict[int, str],
    ) -> Dict[int, str]:
        placeholder_port_mapping = {
            port: f"{NGINX_PLACEHOLDER_SERVICE}" for port in extra_ports
        }

        # Only expose ports defined in nginx_extra_tcp_ports
        port_mapping = {
            port: service_ports.get(port, placeholder_service)
            for port, placeholder_service in placeholder_port_mapping.items()
        }

        missing_ports = [
            str(port) for port in extra_tls_ports if port not in port_mapping
        ]

        if missing_ports:
            raise UserErrors(
                f"Cannot enable TLS on ports {', '.join(missing_ports)} unless they are also set in nginx_extra_tcp_ports"
            )

        return port_mapping


class AWSK8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AWSK8sModuleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        eks_module_refs = get_eks_module_refs(self.layer, module_idx)
        self.module.data["openid_provider_url"] = eks_module_refs[0]
        self.module.data["openid_provider_arn"] = eks_module_refs[1]
        self.module.data["eks_cluster_name"] = eks_module_refs[2]
        super(AWSK8sModuleProcessor, self).process(module_idx)


class GcpK8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GcpK8sModuleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        super(GcpK8sModuleProcessor, self).process(module_idx)


class LocalK8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if system() not in ["Linux", "Darwin"]:
            raise UserErrors(
                "Opta Local is not built to support this host operating system."
            )
        super(LocalK8sModuleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        super(LocalK8sModuleProcessor, self).process(module_idx)


class AWSIamAssembler:
    def __init__(self, *args: Any, **kwargs: Any):
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        self.publish_queues: List[str] = []
        self.subscribe_queues: List[str] = []
        self.publish_topics: List[str] = []
        self.kms_write_keys: List[str] = []
        self.kms_read_keys: List[str] = []
        self.dynamodb_write_tables: List[str] = []
        self.dynamodb_read_tables: List[str] = []
        super(AWSIamAssembler, self).__init__()

    def prepare_iam_statements(self) -> List[dict]:
        iam_statements = []
        if self.read_buckets:
            iam_statements.append(
                AWS.prepare_read_buckets_iam_statements(self.read_buckets)
            )
        if self.write_buckets:
            iam_statements.append(
                AWS.prepare_write_buckets_iam_statements(self.write_buckets)
            )
        if self.publish_queues:
            iam_statements.append(
                AWS.prepare_publish_queues_iam_statements(self.publish_queues)
            )
        if self.subscribe_queues:
            iam_statements.append(
                AWS.prepare_subscribe_queues_iam_statements(self.subscribe_queues)
            )
        if self.publish_topics:
            iam_statements.append(
                AWS.prepare_publish_sns_iam_statements(self.publish_topics)
            )
        if self.kms_write_keys:
            iam_statements.append(
                AWS.prepare_kms_write_keys_statements(self.kms_write_keys)
            )
        if self.kms_read_keys:
            iam_statements.append(
                AWS.prepare_kms_read_keys_statements(self.kms_read_keys)
            )
        if self.dynamodb_write_tables:
            iam_statements.append(
                AWS.prepare_dynamodb_write_tables_statements(self.dynamodb_write_tables)
            )
        if self.dynamodb_read_tables:
            iam_statements.append(
                AWS.prepare_dynamodb_read_tables_statements(self.dynamodb_read_tables)
            )
        return iam_statements

    def handle_sqs_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["publish", "subscribe"]
        for permission in link_permissions:
            if permission == "publish":
                self.publish_queues.append(
                    f"${{{{module.{linked_module.name}.queue_arn}}}}"
                )
                self.kms_write_keys.append(
                    f"${{{{module.{linked_module.name}.kms_arn}}}}"
                )
            elif permission == "subscribe":
                self.subscribe_queues.append(
                    f"${{{{module.{linked_module.name}.queue_arn}}}}"
                )
                self.kms_read_keys.append(f"${{{{module.{linked_module.name}.kms_arn}}}}")
            else:
                raise Exception(f"Invalid permission {permission}")

    def handle_sns_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["publish"]
        for permission in link_permissions:
            if permission == "publish":
                self.publish_topics.append(
                    f"${{{{module.{linked_module.name}.topic_arn}}}}"
                )
                self.kms_write_keys.append(
                    f"${{{{module.{linked_module.name}.kms_arn}}}}"
                )
            else:
                raise Exception(f"Invalid permission {permission}")

    def handle_dynamodb_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.dynamodb_read_tables.append(
                    f"${{{{module.{linked_module.name}.table_arn}}}}"
                )
                self.kms_read_keys.append(f"${{{{module.{linked_module.name}.kms_arn}}}}")
            elif permission == "write":
                self.dynamodb_write_tables.append(
                    f"${{{{module.{linked_module.name}.table_arn}}}}"
                )
                self.kms_write_keys.append(
                    f"${{{{module.{linked_module.name}.kms_arn}}}}"
                )
            else:
                raise Exception(f"Invalid permission {permission}")

    def handle_s3_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        bucket_name = linked_module.data["bucket_name"]
        # If not specified, bucket should get write permissions
        if link_permissions is None or len(link_permissions) == 0:
            link_permissions = ["write"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(bucket_name)
            elif permission == "write":
                self.write_buckets.append(bucket_name)
            else:
                raise Exception(f"Invalid permission {permission}")


def get_eks_module_refs(layer: "Layer", module_idx: int) -> Tuple[str, str, str]:
    from_parent = False
    eks_modules = layer.get_module_by_type("aws-eks", module_idx)
    if len(eks_modules) == 0 and layer.parent is not None:
        from_parent = True
        eks_modules = layer.parent.get_module_by_type("aws-eks")

    if len(eks_modules) == 0:
        raise UserErrors(
            "Did not find the aws-eks module in the layer or the parent layer"
        )
    eks_module = eks_modules[0]
    module_source = (
        "data.terraform_remote_state.parent.outputs"
        if from_parent
        else f"module.{eks_module.name}"
    )
    return (
        f"${{{{{module_source}.k8s_openid_provider_url}}}}",
        f"${{{{{module_source}.k8s_openid_provider_arn}}}}",
        f"${{{{{module_source}.k8s_cluster_name}}}}",
    )


def get_aws_base_module_refs(layer: "Layer") -> Dict[str, str]:
    from_parent = False
    aws_base_modules = layer.get_module_by_type("aws-base")
    if len(aws_base_modules) == 0 and layer.parent is not None:
        from_parent = True
        aws_base_modules = layer.parent.get_module_by_type("aws-base")

    if len(aws_base_modules) == 0:
        raise UserErrors(
            "Did not find the aws-base module in the layer or the parent layer"
        )
    aws_base_module = aws_base_modules[0]
    module_source = (
        "data.terraform_remote_state.parent.outputs"
        if from_parent
        else f"module.{aws_base_module.name}"
    )
    return {
        "kms_account_key_arn": f"${{{{{module_source}.kms_account_key_arn}}}}",
        "kms_account_key_id": f"${{{{{module_source}.kms_account_key_id}}}}",
        "vpc_id": f"${{{{{module_source}.vpc_id}}}}",
        "private_subnet_ids": f"${{{{{module_source}.private_subnet_ids}}}}",
        "public_subnets_ids": f"${{{{{module_source}.public_subnets_ids}}}}",
    }


def reconcile_nginx_extra_ports(*, update_config_map: bool = True) -> Dict[int, str]:
    """
    Runs the pseudo-controller that scans the cluster for Kubernetes services that expose raw TCP ports.
    If :update_config_map is True (default), it will also update the nginx port config map.
    The ConfigMap won't be updated with any ports not already defined in it.

    Returns the port mapping defined by services, in the form of a dict of "external port -> 'namespace/service_name:service_port'"
    """

    services = kubernetes.list_services()

    # Filter out any deleted services or services that don't have the annotation we want
    services = [
        service for service in services if service.metadata.deletion_timestamp is None
    ]

    # Skip services that don't have the annotation
    services = [
        service
        for service in services
        if NGINX_EXTRA_TCP_PORTS_ANNOTATION in (service.metadata.annotations or {})
    ]

    # Give precedence to older services in case of port conflicts
    services.sort(key=lambda svc: svc.metadata.creation_timestamp)

    port_mapping: Dict[int, str] = {}
    for service in services:
        id = f"{service.metadata.namespace}/{service.metadata.name}"

        extra_ports_annotation: str = service.metadata.annotations[
            NGINX_EXTRA_TCP_PORTS_ANNOTATION
        ]

        try:
            extra_ports: Dict[str, str] = json.loads(extra_ports_annotation)
        except json.JSONDecodeError as e:
            logger.warning(
                "Error decoding the %s annotation on service %s",
                NGINX_EXTRA_TCP_PORTS_ANNOTATION,
                id,
                exc_info=e,
            )
            continue

        if not isinstance(extra_ports, dict):
            logger.warning(
                "Contents of the %s annotation not expected format on service %s",
                NGINX_EXTRA_TCP_PORTS_ANNOTATION,
                id,
            )
            continue

        for nginx_port_str, target_port in extra_ports.items():
            try:
                nginx_port = int(nginx_port_str)
            except ValueError:
                logger.warning(
                    "Contents of the %s annotation not expected format (non-int key) on service %s",
                    NGINX_EXTRA_TCP_PORTS_ANNOTATION,
                    id,
                )
                continue

            if nginx_port in port_mapping:
                logger.warning(
                    "Multiple services found that bind to the %i ingress port. Prioritizing oldest service",
                    nginx_port,
                )
                # Skip conflicting ports
                continue

            port_mapping[
                nginx_port
            ] = f"{service.metadata.namespace}/{service.metadata.name}:{target_port}"

    if not update_config_map:
        return port_mapping

    cm = kubernetes.get_config_map(*NGINX_TCP_CONFIGMAP)
    if cm is None:
        # We can't update anything if we don't have the config map
        return port_mapping

    desired_mapping = {str(port): service for port, service in port_mapping.items()}

    # Don't add any keys, and keys that we don't have a service for should be set to the placeholder service
    current_data: Dict[str, str] = cm.data or {}
    desired_data = {
        port: desired_mapping.get(port, NGINX_PLACEHOLDER_SERVICE)
        for port in current_data
    }

    if desired_data != current_data:
        # We don't handle any conficts here (by passing resource version), but we probably don't need to until this is implemented as an actual controller
        kubernetes.update_config_map_data(
            cm.metadata.namespace, cm.metadata.name, desired_data
        )

    # We return port_mapping instead of desired_data because we always want to return services that have "requested" to be mapped,
    # even if nginx hasn't been configured to expose them.
    return port_mapping
