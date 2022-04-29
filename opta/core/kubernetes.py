import base64
import datetime
import time
import traceback
from logging import DEBUG
from os import makedirs, remove
from os.path import dirname, exists, expanduser
from threading import Thread
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, List, Optional, Set

from colored import attr, fg
from kubernetes.client import (
    ApiException,
    AppsV1Api,
    CoreV1Api,
    EventsV1Api,
    EventsV1Event,
    EventsV1EventSeries,
    NetworkingV1Api,
    V1ConfigMap,
    V1DeleteOptions,
    V1Deployment,
    V1DeploymentList,
    V1IngressClass,
    V1IngressClassList,
    V1Namespace,
    V1NamespaceList,
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
from kubernetes.config.kube_config import ENV_KUBECONFIG_PATH_SEPARATOR
from kubernetes.watch import Watch

import opta.constants as constants
from opta.constants import GENERATED_KUBE_CONFIG_DIR, REDS
from opta.exceptions import UserErrors
from opta.utils import logger, yaml
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


def set_kube_config(layer: "Layer") -> None:
    """Create a kubeconfig file to connect to a kubernetes cluster specified in a given layer"""

    if layer.is_stateless_mode() is True:
        if logger.isEnabledFor(DEBUG):
            logger.debug(
                "set_kube_config called in stateless mode, verify implementation. See stack trace below:"
            )
            traceback.print_stack()

    # Make sure the user has the prerequisite CLI tools installed
    # kubectl may not *technically* be required for this opta command to run, but require
    # it anyways since user must install it to access the cluster.
    ensure_installed("kubectl")
    makedirs(GENERATED_KUBE_CONFIG_DIR, exist_ok=True)
    layer.get_cloud_client().set_kube_config()


def purge_opta_kube_config(layer: "Layer") -> None:
    """Delete the kubeconfig file created for a given layer, and also remove it from the default kubeconfig file"""
    kube_config_file_name = layer.get_kube_config_file_name()
    opta_config: dict
    if exists(kube_config_file_name):
        with open(kube_config_file_name) as f:
            opta_config = yaml.load(f)
        remove(kube_config_file_name)
    else:
        return

    default_kube_config_filename = expanduser(
        constants.DEFAULT_KUBECONFIG.split(ENV_KUBECONFIG_PATH_SEPARATOR)[0]
    )
    if not exists(default_kube_config_filename):
        return

    with open(default_kube_config_filename) as f:
        default_kube_config = yaml.load(f) or {}

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
            for i, x in enumerate(default_kube_config.get(key, []))
            if x["name"] == opta_value["name"]
        ]
        for index in sorted(current_indices, reverse=True):
            del default_kube_config[key][index]

    if default_kube_config.get("current-context") == opta_config_context["name"]:
        default_kube_config["current-context"] = ""
    with open(default_kube_config_filename, "w") as f:
        yaml.dump(default_kube_config, f)


def load_opta_kube_config_to_default(layer: "Layer") -> None:
    kube_config_file_name = layer.get_kube_config_file_name()
    if not exists(kube_config_file_name):
        logger.debug(
            f"Can not find opta managed kube config, {kube_config_file_name}, to load to user default"
        )
        return

    with open(kube_config_file_name) as f:
        opta_config = yaml.load(f)

    default_kube_config_filename = expanduser(
        constants.DEFAULT_KUBECONFIG.split(ENV_KUBECONFIG_PATH_SEPARATOR)[0]
    )
    logger.debug(f"Checking kube config file of {default_kube_config_filename}")
    if not exists(default_kube_config_filename):
        logger.debug("The kube config file did not exist")
        makedirs(dirname(default_kube_config_filename), exist_ok=True)
        with open(default_kube_config_filename, "w") as f:
            yaml.dump(opta_config, f)
        return
    logger.debug("Loading kube config file")
    with open(default_kube_config_filename) as f:
        default_kube_config = yaml.load(f)

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


def get_cluster_name(layer: "Layer") -> str:
    return f"opta-{layer.root().name}"


def cluster_exist(layer: "Layer") -> bool:
    if layer.is_stateless_mode() is True:
        if logger.isEnabledFor(DEBUG):
            logger.debug(
                "cluster_exist called in stateless mode, verify implementation. See stack trace below:"
            )
            traceback.print_stack()
            return False
    return layer.get_cloud_client().cluster_exist()


def load_opta_kube_config() -> None:
    load_kube_config(
        config_file=constants.GENERATED_KUBE_CONFIG or constants.DEFAULT_KUBECONFIG
    )


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


def check_if_namespace_exists(layer_name: str) -> bool:
    load_opta_kube_config()
    v1 = CoreV1Api()
    namespaces = v1.list_namespace(field_selector=f"metadata.name={layer_name}")
    return len(namespaces.items) != 0


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


def check_if_secret_exists(namespace: str, secret_name: str) -> bool:
    """create the secret in the namespace if it doesn't exist"""
    load_opta_kube_config()
    v1 = CoreV1Api()
    secrets: V1SecretList = v1.list_namespaced_secret(
        namespace, field_selector=f"metadata.name={secret_name}"
    )
    return len(secrets.items) != 0


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


def delete_secret_key(namespace: str, secret_name: str, entry_name: str) -> None:
    """
    remove secret from secret store.

    create the secret if it doesn't exist yet.
    """
    load_opta_kube_config()
    v1 = CoreV1Api()
    if not check_if_secret_exists(namespace, secret_name):
        return
    current_secret_object: V1Secret = v1.read_namespaced_secret(secret_name, namespace)
    current_secret_object.data = current_secret_object.data or {}
    current_secret_object.data.pop(entry_name, None)
    v1.replace_namespaced_secret(secret_name, namespace, current_secret_object)


def list_namespaces() -> List[V1Namespace]:
    load_opta_kube_config()
    v1 = CoreV1Api()
    try:
        namespaces: V1NamespaceList = v1.list_namespace()
    except ApiException as e:
        if e.reason == "Unauthorized" or e.status == 401:
            raise UserErrors("User does not have access to Kubernetes Cluster.")

        raise

    return namespaces.items


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


def do_not_show_event(event: EventsV1Event) -> bool:
    return (
        "unable to get metrics" in event.note or "did not receive metrics" in event.note
    )


def _event_last_observed(event: EventsV1Event) -> datetime.datetime:
    """
    Returns the last time an event was observed
    """

    if event.series:
        series_data: EventsV1EventSeries = event.series
        return series_data.last_observed_time

    if event.event_time:
        return event.event_time

    # Fall back to event creation
    return event.metadata.creation_timestamp


def tail_namespace_events(
    layer: "Layer",
    earliest_event_start_time: Optional[datetime.datetime] = None,
    color_idx: int = 15,  # White Color
) -> None:
    load_opta_kube_config()
    v1 = EventsV1Api()
    watch = Watch()
    print(f"{fg(color_idx)}Showing events for namespace {layer.name}{attr(0)}")
    retry_count = 0
    old_events: List[EventsV1Event] = v1.list_namespaced_event(namespace=layer.name).items
    # Filter by time
    if earliest_event_start_time is not None:
        # Redefine so mypy doesn't complain about earliest_event_start_time being Optional during lambda call
        filter_start_time = earliest_event_start_time

        old_events = list(
            filter(lambda x: _event_last_observed(x) > filter_start_time, old_events,)
        )
    # Sort by timestamp
    old_events = sorted(old_events, key=lambda x: _event_last_observed(x))
    event: EventsV1Event
    for event in old_events:
        if do_not_show_event(event):
            continue
        earliest_event_start_time = _event_last_observed(event)
        print(
            f"{fg(color_idx)}{earliest_event_start_time} Namespace {layer.name} event: {event.note}{attr(0)}"
        )
    deleted_pods = set()
    while True:
        try:
            for stream_obj in watch.stream(
                v1.list_namespaced_event, namespace=layer.name,
            ):
                event = stream_obj["object"]
                event_time = _event_last_observed(event)
                if (
                    earliest_event_start_time is None
                    or event_time > earliest_event_start_time
                ):
                    if "Deleted pod:" in event.note:
                        deleted_pods.add(event.note.split(" ")[-1])
                    involved_object: Optional[V1ObjectReference] = event.regarding
                    if (
                        involved_object is not None
                        and involved_object.kind == "Pod"
                        and involved_object.name in deleted_pods
                    ):
                        continue
                    if do_not_show_event(event):
                        continue
                    print(
                        f"{fg(color_idx)}{event_time} Namespace {layer.name} event: {event.note}{attr(0)}"
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
            # print(sys.exc_info()[2])
            logger.error(
                f"{fg(color_idx)}Got the following error while trying to fetch the events in namespace {layer.name}: {e}{attr(0)}"
            )
            logger.debug("Event watch exception", exc_info=True)
            return


def list_deployment(namespace: str) -> List[V1Deployment]:
    """list_deployment

    list objects of kind Deployment

    :param str namespace: namespace to search in.
    """
    load_opta_kube_config()
    apps_client = AppsV1Api()
    deployment_list: V1DeploymentList = apps_client.list_namespaced_deployment(
        namespace=namespace
    )
    return deployment_list.items


def restart_deployment(namespace: str, deployment: str) -> None:
    """restart_deployment

    restart the deployment in the specified namespace, this will honnor the update strategy

    :param str namespace: namespace to search in.
    :param deployment the name of deployment to restart
    """

    load_opta_kube_config()
    apps_client = AppsV1Api()

    logger.debug(f"Restarting deployment '{deployment}' in namespace '{namespace}'")
    # note this is similar implementation to kubectl rollout restart
    # https://github.com/kubernetes/kubectl/blob/release-1.22/pkg/polymorphichelpers/objectrestarter.go#L41
    now = str(datetime.datetime.utcnow().isoformat("T") + "Z")
    body = {
        "spec": {
            "template": {
                "metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": now}}
            }
        }
    }
    apps_client.patch_namespaced_deployment(deployment, namespace, body)


def restart_deployments(namespace: str) -> None:
    """restart_deployments

    restart all deployments in the specified namespace, this will honnor the update strategy

    :param str namespace: namespace to search in.
    """
    deployments = list_deployment(namespace)
    for deploy in deployments:
        logger.info(f"Restarting deployment {deploy.metadata.name}")
        restart_deployment(namespace, deploy.metadata.name)


def list_ingress_classes() -> List[V1IngressClass]:
    load_opta_kube_config()
    networking_client = NetworkingV1Api()

    logger.debug("Listing ingress classes")
    ingress_classes: V1IngressClassList = networking_client.list_ingress_class()
    return ingress_classes.items


# Monkey patch EventsV1Event.event_time to skip `not None` validation in setter.
# See https://github.com/kubernetes-client/python/issues/1616
def event_time_property_get_patch(self: EventsV1Event) -> Any:
    return self._event_time


def event_time_property_set_patch(self: EventsV1Event, value: Any) -> Any:
    self._event_time = value


EventsV1Event.event_time = property(
    fget=event_time_property_get_patch, fset=event_time_property_set_patch
)
