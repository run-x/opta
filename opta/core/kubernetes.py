import base64
import datetime
import time
from os import makedirs, remove
from os.path import exists, expanduser, getmtime
from shutil import which
from subprocess import DEVNULL  # nosec
from threading import Thread
from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional, Set, Tuple

import boto3
from botocore.config import Config
from colored import attr, fg
from google.cloud.container_v1 import ClusterManagerClient
from kubernetes.client import (
    ApiException,
    AppsV1Api,
    CoreV1Api,
    V1ConfigMap,
    V1DeleteOptions,
    V1Deployment,
    V1DeploymentList,
    V1Event,
    V1Namespace,
    V1ObjectMeta,
    V1ObjectReference,
    V1PersistentVolumeClaim,
    V1Pod,
    V1Secret,
    V1SecretList,
    V1Service,
    V1ServiceList,
)
from kubernetes.config import load_kube_config
from kubernetes.config.kube_config import (
    ENV_KUBECONFIG_PATH_SEPARATOR,
    KUBE_CONFIG_DEFAULT_LOCATION,
)
from kubernetes.watch import Watch
from mypy_boto3_eks import EKSClient

from opta.constants import REDS, yaml
from opta.core.gcp import GCP
from opta.core.terraform import get_terraform_outputs
from opta.exceptions import UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import logger
from opta.utils.dependencies import ensure_installed

if TYPE_CHECKING:
    from opta.layer import Layer

GENERATED_KUBE_CONFIG: Optional[str] = None
HOME = expanduser("~")
GENERATED_KUBE_CONFIG_DIR = f"{HOME}/.opta/kubeconfigs"
ONE_WEEK_UNIX = 604800


def get_required_path_executables(cloud: str) -> FrozenSet[str]:
    exec_map = {
        "aws": {"aws"},
        "google": {"gcloud"},
        "azurerm": {"az"},
    }

    return frozenset({"kubectl"}) | exec_map.get(cloud, set())


def set_kube_config(layer: "Layer") -> None:
    """Create a kubeconfig file to connect to a kubernetes cluster specified in a given layer"""
    # Make sure the user has the prerequisite CLI tools installed
    # kubectl may not *technically* be required for this opta command to run, but require
    # it anyways since user must install it to access the cluster.
    ensure_installed("kubectl")
    makedirs(GENERATED_KUBE_CONFIG_DIR, exist_ok=True)
    if layer.cloud == "aws":
        _aws_set_kube_config(layer)
    elif layer.cloud == "google":
        _gcp_set_kube_config(layer)
    elif layer.cloud == "azurerm":
        _azure_set_kube_config(layer)
    elif layer.cloud == "local":
        _local_set_kube_config(layer)


def purge_opta_kube_config(layer: "Layer") -> None:
    """Delete the kubeconfig file created for a given layer, and also remove it from the default kubeconfig file"""
    config_file_name = get_config_file_name(layer)
    opta_config: dict
    if exists(config_file_name):
        opta_config = yaml.load(open(config_file_name))
        remove(config_file_name)
    else:
        return

    default_kube_config_filename = expanduser(
        KUBE_CONFIG_DEFAULT_LOCATION.split(ENV_KUBECONFIG_PATH_SEPARATOR)[0]
    )
    if not exists(default_kube_config_filename):
        return

    default_kube_config = yaml.load(open(default_kube_config_filename))
    opta_config_user = opta_config["users"][0]
    opta_config_context = opta_config["contexts"][0]
    opta_config_cluster = opta_config["clusters"][0]
    for opta_value, key in [
        [opta_config_user, "users"],
        [opta_config_context, "contexts"],
        [opta_config_cluster, "clusters"],
    ]:
        current_indices = [
            i
            for i, x in enumerate(default_kube_config[key])
            if x["name"] == opta_value["name"]
        ]
        for index in sorted(current_indices, reverse=True):
            del default_kube_config[key][index]

    if default_kube_config["current-context"] == opta_config_context["name"]:
        default_kube_config["current-context"] = ""
    with open(default_kube_config_filename, "w") as f:
        yaml.dump(default_kube_config, f)


def _local_set_kube_config(layer: "Layer") -> None:
    nice_run(
        ["kubectl", "config", "use-context", "kind-opta-local-cluster"],
        check=True,
        capture_output=True,
    ).stdout


def get_config_file_name(layer: "Layer") -> str:
    config_file_name = (
        f"{GENERATED_KUBE_CONFIG_DIR}/kubeconfig-{layer.root().name}-{layer.cloud}.yaml"
    )
    return config_file_name


def load_opta_kube_config_to_default(layer: "Layer") -> None:
    config_file_name = get_config_file_name(layer)
    if not exists(config_file_name):
        logger.debug(
            f"Can not find opta managed kube config, {config_file_name}, to load to user default"
        )
        return
    opta_config = yaml.load(open(config_file_name))
    default_kube_config_filename = expanduser(
        KUBE_CONFIG_DEFAULT_LOCATION.split(ENV_KUBECONFIG_PATH_SEPARATOR)[0]
    )
    if not exists(default_kube_config_filename):
        with open(expanduser(default_kube_config_filename), "w") as f:
            yaml.dump(opta_config, f)
        return
    default_kube_config = yaml.load(open(default_kube_config_filename))
    opta_config_user = opta_config["users"][0]
    opta_config_context = opta_config["contexts"][0]
    opta_config_cluster = opta_config["clusters"][0]

    user_indices = [
        i
        for i, x in enumerate(default_kube_config["users"])
        if x["name"] == opta_config_user["name"]
    ]
    if user_indices:
        default_kube_config["users"][user_indices[0]] = opta_config_user
    else:
        default_kube_config["users"].append(opta_config_user)

    context_indices = [
        i
        for i, x in enumerate(default_kube_config["contexts"])
        if x["name"] == opta_config_context["name"]
    ]
    if context_indices:
        default_kube_config["contexts"][context_indices[0]] = opta_config_context
    else:
        default_kube_config["contexts"].append(opta_config_context)

    cluster_indices = [
        i
        for i, x in enumerate(default_kube_config["clusters"])
        if x["name"] == opta_config_cluster["name"]
    ]
    if cluster_indices:
        default_kube_config["clusters"][context_indices[0]] = opta_config_cluster
    else:
        default_kube_config["clusters"].append(opta_config_cluster)

    default_kube_config["current-context"] = opta_config_context["name"]
    with open(default_kube_config_filename, "w") as f:
        yaml.dump(default_kube_config, f)


def _gcp_set_kube_config(layer: "Layer") -> None:
    ensure_installed("gcloud")
    config_file_name = get_config_file_name(layer)
    global GENERATED_KUBE_CONFIG
    if exists(config_file_name):
        if getmtime(config_file_name) > time.time() - ONE_WEEK_UNIX:
            GENERATED_KUBE_CONFIG = config_file_name
            return
        else:
            remove(config_file_name)

    gcp = GCP(layer=layer)
    credentials = gcp.get_credentials()[0]
    region, project_id = _gcp_get_cluster_env(layer.root())
    cluster_name = get_cluster_name(layer.root())
    gke_client = ClusterManagerClient(credentials=credentials)
    cluster_data = gke_client.get_cluster(
        name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
    )

    cluster_ca_certificate = cluster_data.master_auth.cluster_ca_certificate
    cluster_endpoint = f"https://{cluster_data.endpoint}"
    gcloud_path = which("gcloud")
    kube_config_resource_name = f"{project_id}_{region}_{cluster_name}"

    cluster_config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "cluster": {
                    "server": cluster_endpoint,
                    "certificate-authority-data": cluster_ca_certificate,
                },
                "name": kube_config_resource_name,
            }
        ],
        "contexts": [
            {
                "context": {
                    "cluster": kube_config_resource_name,
                    "user": kube_config_resource_name,
                },
                "name": kube_config_resource_name,
            }
        ],
        "current-context": kube_config_resource_name,
        "preferences": {},
        "users": [
            {
                "name": kube_config_resource_name,
                "user": {
                    "auth-provider": {
                        "name": "gcp",
                        "config": {
                            "cmd-args": "config config-helper --format=json",
                            "cmd-path": gcloud_path,
                            "expiry-key": "{.credential.token_expiry}",
                            "token-key": "{.credential.access_token}",
                        },
                    }
                },
            }
        ],
    }
    with open(config_file_name, "w") as f:
        yaml.dump(cluster_config, f)
    GENERATED_KUBE_CONFIG = config_file_name
    return


def _azure_set_kube_config(layer: "Layer") -> None:
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


def _aws_set_kube_config(layer: "Layer") -> None:
    config_file_name = get_config_file_name(layer)
    global GENERATED_KUBE_CONFIG
    if exists(config_file_name):
        if getmtime(config_file_name) > time.time() - ONE_WEEK_UNIX:
            GENERATED_KUBE_CONFIG = config_file_name
            return
        else:
            remove(config_file_name)

    region, account_id = _aws_get_cluster_env(layer.root())

    # Get the environment's account details from the opta config
    root_layer = layer.root()
    cluster_name = get_cluster_name(root_layer)

    if cluster_name is None:
        raise Exception(
            "The EKS cluster name could not be determined -- please make sure it has been applied in the environment."
        )

    client: EKSClient = boto3.client("eks", config=Config(region_name=region))

    # get cluster details
    cluster = client.describe_cluster(name=cluster_name)
    cluster_cert = cluster["cluster"]["certificateAuthority"]["data"]
    cluster_ep = cluster["cluster"]["endpoint"]
    kube_config_resource_name = f"{account_id}_{region}_{cluster_name}"

    cluster_config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "cluster": {
                    "server": str(cluster_ep),
                    "certificate-authority-data": str(cluster_cert),
                },
                "name": kube_config_resource_name,
            }
        ],
        "contexts": [
            {
                "context": {
                    "cluster": kube_config_resource_name,
                    "user": kube_config_resource_name,
                },
                "name": kube_config_resource_name,
            }
        ],
        "current-context": kube_config_resource_name,
        "preferences": {},
        "users": [
            {
                "name": kube_config_resource_name,
                "user": {
                    "exec": {
                        "apiVersion": "client.authentication.k8s.io/v1alpha1",
                        "command": "aws",
                        "args": [
                            "--region",
                            region,
                            "eks",
                            "get-token",
                            "--cluster-name",
                            cluster_name,
                        ],
                        "env": None,
                    }
                },
            }
        ],
    }
    with open(config_file_name, "w") as f:
        yaml.dump(cluster_config, f)
    GENERATED_KUBE_CONFIG = config_file_name
    return


def get_cluster_name(layer: "Layer") -> Optional[str]:
    outputs = get_terraform_outputs(layer)
    cluster_name = outputs.get("parent.k8s_cluster_name") or outputs.get(
        "k8s_cluster_name"
    )
    return cluster_name


def _aws_get_cluster_env(root_layer: "Layer") -> Tuple[str, str]:
    aws_provider = root_layer.providers["aws"]
    return aws_provider["region"], aws_provider["account_id"]


def _gcp_get_cluster_env(root_layer: "Layer") -> Tuple[str, str]:
    googl_provider = root_layer.providers["google"]
    return googl_provider["region"], googl_provider["project"]


def load_opta_kube_config() -> None:
    load_kube_config(config_file=GENERATED_KUBE_CONFIG or KUBE_CONFIG_DEFAULT_LOCATION)


def current_image_digest_tag(layer: "Layer") -> dict:
    image_info = {"digest": None, "tag": None}
    load_opta_kube_config()
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
    load_opta_kube_config()
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


def create_secret_if_not_exists(namespace: str, secret_name: str) -> None:
    """create the secret in the namespace if it doesn't exist"""
    load_opta_kube_config()
    v1 = CoreV1Api()
    secrets: V1SecretList = v1.list_namespaced_secret(
        namespace, field_selector=f"metadata.name={secret_name}"
    )
    if len(secrets.items) == 0:
        v1.create_namespaced_secret(
            namespace, body=V1Secret(metadata=V1ObjectMeta(name=secret_name))
        )


def get_namespaced_secrets(namespace: str, secret_name: str) -> dict:
    """read the specified Secret"""
    load_opta_kube_config()
    v1 = CoreV1Api()
    try:
        api_response = v1.read_namespaced_secret(secret_name, namespace)
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


def update_secrets(namespace: str, secret_name: str, new_values: dict) -> None:
    """
    append the new values to the existing data for this secret.

    create the secret if it doesn't exist yet.
    """
    load_opta_kube_config()
    v1 = CoreV1Api()
    create_secret_if_not_exists(namespace, secret_name)
    current_secret_object: V1Secret = v1.read_namespaced_secret(secret_name, namespace)
    current_secret_object.data = current_secret_object.data or {}
    for k, v in new_values.items():
        current_secret_object.data[k] = base64.b64encode(v.encode("utf-8")).decode(
            "utf-8"
        )
    v1.replace_namespaced_secret(secret_name, namespace, current_secret_object)


def list_namespaces() -> None:
    load_opta_kube_config()
    v1 = CoreV1Api()
    try:
        v1.list_namespace()
    except ApiException as e:
        if e.reason == "Unauthorized" or e.status == 401:
            raise UserErrors("User does not have access to Kubernetes Cluster.")


def list_persistent_volume_claims(
    *, namespace: Optional[str] = None, opta_managed: bool = False
) -> List[V1PersistentVolumeClaim]:
    """list_persistent_volume_claims

    list objects of kind PersistentVolumeClaim

    :param str namespace: namespace to search in. If not set, search all namespaces
    :param bool opta_managed: filter to only returned objects managed by opta
    """
    load_opta_kube_config()
    v1 = CoreV1Api()

    if namespace:
        claims = v1.list_namespaced_persistent_volume_claim(namespace)
    else:
        claims = v1.list_persistent_volume_claim_for_all_namespaces()

    # Filter out any claims that are not managed by opta
    claim_items = claims.items
    if opta_managed:
        claim_items = [
            claim for claim in claim_items if claim.metadata.name.startswith("opta-")
        ]

    return claim_items


def delete_persistent_volume_claim(
    namespace: str, name: str, async_req: bool = False
) -> None:
    """delete_persistent_volume_claim

    delete a PersistentVolumeClaim

    This method makes a synchronous HTTP request by default. To make an
    asynchronous HTTP request, please pass async_req=True

    :param str namespace: namespace where the PersistentVolumeClaim is located
    :param str name: name of the PersistentVolumeClaim (required)
    :param bool async_req: execute request asynchronously
    """
    load_opta_kube_config()
    v1 = CoreV1Api()

    try:
        options = V1DeleteOptions(grace_period_seconds=5)
        v1.delete_collection_namespaced_persistent_volume_claim(
            namespace=namespace,
            field_selector=f"metadata.name={name}",
            async_req=async_req,
            body=options,
        )
    except ApiException as e:
        if e.status == 404:
            # not found = nothing to delete
            return None
        raise e


def delete_persistent_volume_claims(
    namespace: str, opta_managed: bool = True, async_req: bool = True
) -> None:
    """delete_persistent_volume_claims

    Delete Persistent Volume Claims for a given namespace

    This method makes a synchronous HTTP request by default. To make an
    asynchronous HTTP request, please pass async_req=True

    :param str namespace: namespace to search for the Persistent Volume Claims
    :param bool opta_managed: filter to only delete objects managed by opta
    :param bool async_req: execute request asynchronously
    """

    claims = list_persistent_volume_claims(namespace=namespace, opta_managed=opta_managed)
    if not claims:
        logger.debug(
            f"No persistent volume claim (opta_managed: {opta_managed}) found in namespace '{namespace}', skipping persistent volume cleanup"
        )
        return

    logger.info(f"Deleting persistent volumes in namespace '{namespace}'")

    # delete the PVCs
    # Note: when deleting the PVC, the PV are automatically deleted
    for claim in claims:
        logger.info(f"Deleting persistent volume claim '{claim.metadata.name}'")
        delete_persistent_volume_claim(
            namespace, claim.metadata.name, async_req=async_req
        )


def list_services(*, namespace: Optional[str] = None) -> List[V1Service]:
    load_opta_kube_config()
    v1 = CoreV1Api()

    services: V1ServiceList
    if namespace:
        services = v1.list_namespaced_service(namespace)
    else:
        services = v1.list_service_for_all_namespaces()

    return services.items


def get_config_map(namespace: str, name: str) -> V1ConfigMap:
    load_opta_kube_config()
    v1 = CoreV1Api()
    try:
        cm: V1ConfigMap = v1.read_namespaced_config_map(name, namespace)
    except ApiException as e:
        if e.status == 404:
            return None

        raise

    return cm


def update_config_map_data(namespace: str, name: str, data: Dict[str, str]) -> None:
    load_opta_kube_config()
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


def tail_module_log(
    layer: "Layer",
    module_name: str,
    since_seconds: Optional[int] = None,
    earliest_pod_start_time: Optional[datetime.datetime] = None,
    start_color_idx: int = 15,  # White Color
) -> None:
    current_pods_monitored: Set[str] = set()
    load_opta_kube_config()
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
        if color_idx in REDS:
            count += 1
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
    color_idx: int = 15,  # White Color
) -> None:
    load_opta_kube_config()
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
