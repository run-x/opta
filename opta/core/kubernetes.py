import base64
import datetime
import time
from subprocess import DEVNULL
from threading import Thread
from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional, Set, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from colored import attr, fg
from kubernetes.client import (
    ApiException,
    AppsV1Api,
    CoreV1Api,
    V1ConfigMap,
    V1Deployment,
    V1DeploymentList,
    V1Event,
    V1Namespace,
    V1ObjectMeta,
    V1ObjectReference,
    V1Pod,
    V1Secret,
    V1SecretList,
    V1Service,
    V1ServiceList,
)
from kubernetes.config import load_kube_config
from kubernetes.watch import Watch

from opta.core.gcp import GCP
from opta.core.terraform import get_terraform_outputs
from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import deep_merge, fmt_msg, logger
from opta.utils.dependencies import ensure_installed

if TYPE_CHECKING:
    from opta.layer import Layer


def get_required_path_executables(cloud: str) -> FrozenSet[str]:
    exec_map = {
        "aws": {"aws"},
        "google": {"gcloud"},
        "azurerm": {"az"},
    }

    return frozenset({"kubectl"}) | exec_map.get(cloud, set())


def configure_kubectl(layer: "Layer") -> None:
    """Configure the kubectl CLI tool for the given layer"""
    # Make sure the user has the prerequisite CLI tools installed
    # kubectl may not *technically* be required for this opta command to run, but require
    # it anyways since user must install it to access the cluster.
    ensure_installed("kubectl")
    if layer.cloud == "aws":
        _aws_configure_kubectl(layer)
    elif layer.cloud == "google":
        _gcp_configure_kubectl(layer)
    elif layer.cloud == "azurerm":
        _azure_configure_kubectl(layer)
    elif layer.cloud == "local":
        _local_configure_kubectl(layer)


def _local_configure_kubectl(layer: "Layer") -> None:
    nice_run(
        ["kubectl", "config", "use-context", "kind-opta-local-cluster"],
        check=True,
        capture_output=True,
    ).stdout


def _gcp_configure_kubectl(layer: "Layer") -> None:
    ensure_installed("gcloud")

    try:
        if GCP.using_service_account():
            service_account_key_path = GCP.get_service_account_key_path()
            nice_run(
                [
                    "gcloud",
                    "auth",
                    "activate-service-account",
                    "--key-file",
                    service_account_key_path,
                ]
            )

        out: str = nice_run(
            ["gcloud", "config", "get-value", "project"], check=True, capture_output=True,
        ).stdout
    except Exception as err:
        raise UserErrors(
            fmt_msg(
                f"""
                Running the gcloud CLI failed. Please make sure you've properly
                configured your gcloud credentials, and recently refreshed them if
                they're expired:
                ~{err}
                """
            )
        )
    current_project_id = out.strip()

    root_layer = layer.root()
    env_gcp_region, env_gcp_project = _gcp_get_cluster_env(root_layer)
    if env_gcp_project != current_project_id:
        raise UserErrors(
            fmt_msg(
                f"""
                The gcloud CLI is not configured with the right credentials to
                access the {root_layer.name or ""} cluster.
                ~Current GCP project: {current_project_id}
                ~Expected GCP project: {env_gcp_project}
                """
            )
        )

    cluster_name = get_cluster_name(root_layer)

    if cluster_name is None:
        raise Exception(
            "The GKE cluster name could not be determined -- please make sure it has been applied in the environment."
        )

    # Update kubeconfig with the cluster details, and also switches context
    nice_run(
        [
            "gcloud",
            "container",
            "clusters",
            "get-credentials",
            cluster_name,
            f"--region={env_gcp_region}",
        ],
        stdout=DEVNULL,
        check=True,
    )


def _azure_configure_kubectl(layer: "Layer") -> None:
    root_layer = layer.root()
    providers = root_layer.gen_providers(0)

    ensure_installed("az")

    rg_name = providers["terraform"]["backend"]["azurerm"]["resource_group_name"]
    cluster_name = get_cluster_name(root_layer)

    if not cluster_name:
        raise Exception(
            "The AKS cluster name could not be determined -- please make sure it has been applied in the environment."
        )

    nice_run(
        [
            "az",
            "aks",
            "get-credentials",
            "--resource-group",
            rg_name,
            "--name",
            cluster_name,
            "--admin",
            "--overwrite-existing",
        ],
        stdout=DEVNULL,
        check=True,
    )


def _aws_configure_kubectl(layer: "Layer") -> None:
    ensure_installed("aws")

    # Get the current account details from the AWS CLI.
    try:
        aws_caller_identity = boto3.client("sts").get_caller_identity()
    except NoCredentialsError:
        raise UserErrors(
            "Unable to locate credentials.\n"
            "Visit `https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html` "
            "for more information."
        )
    except ClientError as e:
        raise UserErrors(
            "The AWS Credentials are not configured properly.\n"
            f" - Code: {e.response['Error']['Code']} Error Message: {e.response['Error']['Message']}"
            "Visit `https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html` "
            "for more information."
        )

    current_aws_account_id = aws_caller_identity["Account"]

    # Get the environment's account details from the opta config
    root_layer = layer.root()
    env_aws_region, env_aws_account_ids = _aws_get_cluster_env(root_layer)

    # Make sure the current account points to the cluster environment
    if str(current_aws_account_id) not in env_aws_account_ids:
        raise UserErrors(
            fmt_msg(
                f"""
                The AWS CLI is not configured with the right credentials to
                access the {root_layer.name or ""} cluster.
                ~Current AWS Account ID: {current_aws_account_id}
                ~Valid AWS Account IDs: {env_aws_account_ids}
                """
            )
        )

    cluster_name = get_cluster_name(root_layer)

    if cluster_name is None:
        raise Exception(
            "The EKS cluster name could not be determined -- please make sure it has been applied in the environment."
        )

    # Update kubeconfig with the cluster details, and also switches context
    # TODO: Change AWS to BOTO3
    nice_run(
        [
            "aws",
            "eks",
            "update-kubeconfig",
            "--name",
            cluster_name,
            "--region",
            env_aws_region,
        ],
        stdout=DEVNULL,
        check=True,
    )


def get_cluster_name(layer: "Layer") -> Optional[str]:
    outputs = get_terraform_outputs(layer)
    cluster_name = outputs.get("parent.k8s_cluster_name") or outputs.get(
        "k8s_cluster_name"
    )
    return cluster_name


def _aws_get_cluster_env(root_layer: "Layer") -> Tuple[str, List[str]]:
    aws_provider = root_layer.providers["aws"]
    return aws_provider["region"], [aws_provider["account_id"]]


def _gcp_get_cluster_env(root_layer: "Layer") -> Tuple[str, str]:
    googl_provider = root_layer.providers["google"]
    return googl_provider["region"], googl_provider["project"]


def current_image_digest_tag(layer: "Layer") -> dict:
    image_info = {"digest": None, "tag": None}
    load_kube_config()
    apps_client = AppsV1Api()
    deployment_list: V1DeploymentList = apps_client.list_namespaced_deployment(
        namespace=layer.name
    )
    if len(deployment_list.items) > 0:
        deployment: V1Deployment = deployment_list.items[0]
        image_parts = deployment.spec.template.spec.containers[0].image.split("@")
        if len(image_parts) == 2:
            image_info["digest"] = image_parts[-1]
            return image_info
        image_parts = deployment.spec.template.spec.containers[0].image.split(":")
        if len(image_parts) == 2:
            image_info["tag"] = image_parts[-1]
            return image_info
    return image_info


def create_namespace_if_not_exists(layer_name: str) -> None:
    load_kube_config()
    v1 = CoreV1Api()
    namespaces = v1.list_namespace(field_selector=f"metadata.name={layer_name}")
    if len(namespaces.items) == 0:
        v1.create_namespace(
            body=V1Namespace(
                metadata=V1ObjectMeta(
                    name=layer_name, annotations={"linkerd.io/inject": "enabled"}
                )
            )
        )


def create_manual_secrets_if_not_exists(layer_name: str) -> None:
    load_kube_config()
    v1 = CoreV1Api()
    manual_secrets: V1SecretList = v1.list_namespaced_secret(
        layer_name, field_selector="metadata.name=manual-secrets"
    )
    if len(manual_secrets.items) == 0:
        v1.create_namespaced_secret(
            layer_name, body=V1Secret(metadata=V1ObjectMeta(name="manual-secrets"))
        )


def get_manual_secrets(layer_name: str) -> dict:
    load_kube_config()
    v1 = CoreV1Api()
    try:
        api_response = v1.read_namespaced_secret("manual-secrets", layer_name)
    except ApiException as e:
        if e.status == 404:
            return {}
        raise e
    return (
        {}
        if api_response.data is None
        else {
            k: base64.b64decode(v).decode("utf-8") for k, v in api_response.data.items()
        }
    )


def update_manual_secrets(layer_name: str, new_values: dict) -> None:
    load_kube_config()
    v1 = CoreV1Api()
    create_manual_secrets_if_not_exists(layer_name)
    current_secret_object: V1Secret = v1.read_namespaced_secret(
        "manual-secrets", layer_name
    )
    current_secret_object.data = current_secret_object.data or {}
    for k, v in new_values.items():
        current_secret_object.data[k] = base64.b64encode(v.encode("utf-8")).decode(
            "utf-8"
        )
    v1.replace_namespaced_secret("manual-secrets", layer_name, current_secret_object)


def get_linked_secrets(layer_name: str) -> dict:
    load_kube_config()
    v1 = CoreV1Api()
    try:
        api_response = v1.read_namespaced_secret("secret", layer_name)
    except ApiException as e:
        if e.status == 404:
            return {}
        raise e
    return (
        {}
        if api_response.data is None
        else {
            k: base64.b64decode(v).decode("utf-8") for k, v in api_response.data.items()
        }
    )


def list_namespaces() -> None:
    load_kube_config()
    v1 = CoreV1Api()
    try:
        v1.list_namespace()
    except ApiException as e:
        if e.reason == "Unauthorized" or e.status == 401:
            raise UserErrors("User does not have access to Kubernetes Cluster.")


def list_services(*, namespace: Optional[str] = None) -> List[V1Service]:
    load_kube_config()
    v1 = CoreV1Api()

    services: V1ServiceList
    if namespace:
        services = v1.list_namespaced_service(namespace)
    else:
        services = v1.list_service_for_all_namespaces()

    return services.items


def get_config_map(namespace: str, name: str) -> V1ConfigMap:
    load_kube_config()
    v1 = CoreV1Api()
    try:
        cm: V1ConfigMap = v1.read_namespaced_config_map(name, namespace)
    except ApiException as e:
        if e.status == 404:
            return None

        raise

    return cm


def update_config_map_data(namespace: str, name: str, data: Dict[str, str]) -> None:
    load_kube_config()
    v1 = CoreV1Api()

    # Pulled from https://github.com/kubernetes-client/python/issues/1549#issuecomment-921611078
    manifest = [
        {
            "kind": "ConfigMap",
            "apiVersion": "v1",
            "metadata": {"name": name},
            "op": "replace",
            "path": "/data",
            "value": data,
        }
    ]

    v1.patch_namespaced_config_map(name, namespace, manifest)


def get_secrets(layer_name: str) -> dict:
    return deep_merge(get_manual_secrets(layer_name), get_linked_secrets(layer_name))


def tail_module_log(
    layer: "Layer",
    module_name: str,
    since_seconds: Optional[int] = None,
    earliest_pod_start_time: Optional[datetime.datetime] = None,
    start_color_idx: int = 1,
) -> None:
    current_pods_monitored: Set[str] = set()
    load_kube_config()
    v1 = CoreV1Api()
    watch = Watch()
    count = 0
    """Using the UTC Time stamp as the Kubernetes uses the UTC Timestamps."""
    for event in watch.stream(
        v1.list_namespaced_pod,
        namespace=layer.name,
        label_selector=f"app.kubernetes.io/instance={layer.name}-{module_name}",
    ):
        pod: V1Pod = event["object"]
        color_idx = count % (256 - start_color_idx) + start_color_idx
        if (
            earliest_pod_start_time is not None
            and pod.metadata.creation_timestamp < earliest_pod_start_time
        ):
            continue

        if pod.metadata.name not in current_pods_monitored:
            current_pods_monitored.add(pod.metadata.name)
            new_thread = Thread(
                target=tail_pod_log,
                args=(layer.name, pod, color_idx, since_seconds),
                daemon=True,
            )
            new_thread.start()
            count += 1


def tail_pod_log(
    namespace: str, pod: V1Pod, color_idx: int, seconds: Optional[int]
) -> None:
    v1 = CoreV1Api()
    watch = Watch()
    print(
        f"{fg(color_idx)}Showing the logs for server {pod.metadata.name} of your service{attr(0)}"
    )
    retry_count = 0
    while True:
        try:
            for logline in watch.stream(
                v1.read_namespaced_pod_log,
                name=pod.metadata.name,
                namespace=namespace,
                container="k8s-service",
                since_seconds=seconds,
            ):
                print(f"{fg(color_idx)}{pod.metadata.name} {logline}{attr(0)}")
        except Exception as e:
            if type(e) == ApiException:
                if e.status == 404:  # type: ignore
                    print(
                        f"{fg(color_idx)}Server {pod.metadata.name} has been terminated{attr(0)}"
                    )
                    return

            if retry_count < 15:
                print(
                    f"{fg(color_idx)}Couldn't get logs, waiting a bit and retrying{attr(0)}"
                )
                time.sleep(retry_count)
                retry_count += 1
            else:
                logger.error(
                    f"Got the following error while trying to fetch the logs for pod {pod.metadata.name} in namespace {namespace}: {e}"
                )
                return


def do_not_show_event(event: V1Event) -> bool:
    return (
        "unable to get metrics" in event.message
        or "did not receive metrics" in event.message
    )


def tail_namespace_events(
    layer: "Layer",
    earliest_event_start_time: Optional[datetime.datetime] = None,
    color_idx: int = 1,
) -> None:
    load_kube_config()
    v1 = CoreV1Api()
    watch = Watch()
    print(f"{fg(color_idx)}Showing events for namespace {layer.name}{attr(0)}")
    retry_count = 0
    old_events: List[V1Event] = v1.list_namespaced_event(namespace=layer.name).items
    # Filter by time
    if earliest_event_start_time is not None:
        old_events = list(
            filter(
                lambda x: (x.last_timestamp or x.event_time) > earliest_event_start_time,
                old_events,
            )
        )
    # Sort by timestamp
    old_events = sorted(old_events, key=lambda x: (x.last_timestamp or x.event_time))
    event: V1Event
    for event in old_events:
        if do_not_show_event(event):
            continue
        earliest_event_start_time = event.last_timestamp or event.event_time
        print(
            f"{fg(color_idx)}{event.last_timestamp or event.event_time} Namespace {layer.name} event: {event.message}{attr(0)}"
        )
    deleted_pods = set()
    while True:
        try:
            for stream_obj in watch.stream(
                v1.list_namespaced_event, namespace=layer.name,
            ):
                event = stream_obj["object"]
                if (
                    earliest_event_start_time is None
                    or (event.last_timestamp or event.event_time)
                    > earliest_event_start_time
                ):
                    if "Deleted pod:" in event.message:
                        deleted_pods.add(event.message.split(" ")[-1])
                    involved_object: Optional[V1ObjectReference] = event.involved_object
                    if (
                        involved_object is not None
                        and involved_object.kind == "Pod"
                        and involved_object.name in deleted_pods
                    ):
                        continue
                    if do_not_show_event(event):
                        continue
                    print(
                        f"{fg(color_idx)}{event.last_timestamp or event.event_time} Namespace {layer.name} event: {event.message}{attr(0)}"
                    )
        except ApiException as e:
            if retry_count < 5:
                print(
                    f"{fg(color_idx)}Couldn't get logs, waiting a bit and retrying{attr(0)}"
                )
                time.sleep(1 << retry_count)
                retry_count += 1
            else:
                logger.error(
                    f"{fg(color_idx)}Got the following error while trying to fetch the events in namespace {layer.name}: {e}"
                )
                return
        except Exception as e:
            logger.error(
                f"{fg(color_idx)}Got the following error while trying to fetch the events in namespace {layer.name}: {e}{attr(0)}"
            )
            return
