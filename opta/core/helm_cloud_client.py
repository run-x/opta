import base64
import json
from os.path import exists
from typing import TYPE_CHECKING, Dict, Optional

from kubernetes.client import CoreV1Api, V1Secret, V1SecretList
from kubernetes.config.kube_config import ENV_KUBECONFIG_PATH_SEPARATOR

import opta.constants as constants
from opta.core.cloud_client import CloudClient
from opta.core.kubernetes import (
    check_if_secret_exists,
    create_secret_if_not_exists,
    load_opta_kube_config,
    set_kube_config,
)
from opta.exceptions import LocalNotImplemented, UserErrors
from opta.nice_subprocess import nice_run
from opta.utils import logger, yaml

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class HelmCloudClient(CloudClient):
    def __init__(self, layer: "Layer"):
        super().__init__(layer)

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        set_kube_config(self.layer)
        load_opta_kube_config()
        v1 = CoreV1Api()
        secret_name = f"opta-config-{self.layer.state_storage()}"
        secrets: V1SecretList = v1.list_namespaced_secret(
            "default", field_selector=f"metadata.name={secret_name}"
        )
        if len(secrets.items) == 0:
            return None
        secret: V1Secret = secrets.items[0]
        return json.loads(base64.b64decode(secret.data["config"]).decode("utf-8"))

    def upload_opta_config(self) -> None:
        set_kube_config(self.layer)
        load_opta_kube_config()
        v1 = CoreV1Api()
        secret_name = f"opta-config-{self.layer.state_storage()}"
        create_secret_if_not_exists("default", secret_name)
        current_secret_object: V1Secret = v1.read_namespaced_secret(
            secret_name, "default"
        )
        current_secret_object.data = current_secret_object.data or {}
        current_secret_object.data["config"] = base64.b64encode(
            json.dumps(self.layer.structured_config()).encode("utf-8")
        ).decode("utf-8")
        v1.replace_namespaced_secret(secret_name, "default", current_secret_object)

        return None

    def delete_opta_config(self) -> None:
        set_kube_config(self.layer)
        load_opta_kube_config()
        v1 = CoreV1Api()
        secret_name = f"opta-config-{self.layer.state_storage()}"
        if check_if_secret_exists("default", secret_name):
            v1.delete_namespaced_secret(secret_name, "default")

    def delete_remote_state(self) -> None:
        v1 = CoreV1Api()
        secret_name = f"tfstate-default-{self.layer.state_storage()}"
        if check_if_secret_exists("default", secret_name):
            v1.delete_namespaced_secret(secret_name, "default")

    def get_terraform_lock_id(self) -> str:
        return ""

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        raise LocalNotImplemented(
            "get_all_remote_configs: Feature Unsupported for the BYO K8s feature"
        )

    def set_kube_config(self) -> None:
        kube_config_file_name = self.layer.get_kube_config_file_name()
        default_kube_config_filename = constants.DEFAULT_KUBECONFIG.split(
            ENV_KUBECONFIG_PATH_SEPARATOR
        )[0]
        if not exists(default_kube_config_filename):
            raise UserErrors(
                "To use K8s-native provider, your must have your kubeconfig set"
            )
        logger.debug("Loading kube config file")
        try:
            with open(default_kube_config_filename) as f:
                default_kube_config = yaml.load(f)
        except yaml.YAMLError:
            raise UserErrors(
                f"Could not load your kubeconfig file {default_kube_config_filename} as valid yaml"
            )
        except OSError:
            raise UserErrors(
                f"Could not open your kubeconfig file {default_kube_config_filename}."
            )
        current_context_name = default_kube_config.get("current-context")
        if current_context_name in [None, ""]:
            raise UserErrors("Could not determine current context of your kubeconfig")
        try:
            current_context = next(
                context
                for context in default_kube_config["contexts"]
                if context["name"] == current_context_name
            )
        except StopIteration:
            raise UserErrors(
                f"Could not find the context {current_context_name} in your kubeconfig"
            )
        current_cluster_name = current_context["context"]["cluster"]
        try:
            current_cluster = next(
                cluster
                for cluster in default_kube_config["clusters"]
                if cluster["name"] == current_cluster_name
            )
        except StopIteration:
            raise UserErrors(
                f"Could not find the cluster {current_cluster_name} in your kubeconfig"
            )
        current_user_name = current_context["context"]["user"]
        try:
            current_user = next(
                user
                for user in default_kube_config["users"]
                if user["name"] == current_user_name
            )
        except StopIteration:
            raise UserErrors(
                f"Could not find the user {current_user_name} in your kubeconfig"
            )

        cluster_config = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [current_cluster],
            "contexts": [current_context],
            "current-context": current_context_name,
            "preferences": {},
            "users": [current_user],
        }
        with open(kube_config_file_name, "w") as f:
            yaml.dump(cluster_config, f)
        constants.GENERATED_KUBE_CONFIG = kube_config_file_name

    def cluster_exist(self) -> bool:
        # "kubectl version" returns an error code if it can't connect to a cluster
        try:
            nice_run(["kubectl", "version"], check=True, capture_output=True)
        except Exception:
            raise UserErrors(
                "The current kubectl configuration must be valid if you wanna use the BYO K8s feature"
            )
        return True

    def get_kube_context_name(self) -> str:
        return nice_run(
            ["kubectl", "config", "current-context"], check=True, capture_output=True
        ).stdout.strip()

    def get_remote_state(self) -> str:
        pass
