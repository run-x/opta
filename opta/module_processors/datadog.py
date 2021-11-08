import base64
from typing import TYPE_CHECKING

import click
from kubernetes.client import ApiException, CoreV1Api, V1Namespace, V1ObjectMeta, V1Secret
from kubernetes.config import load_kube_config
from requests import codes, get

from opta.core.kubernetes import configure_kubectl
from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import exp_backoff, logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class DatadogProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "datadog":
            raise Exception(
                f"The module {module.name} was expected to be of type datadog"
            )
        # If the k8s cluster was recently created, it may take some time for it to be ready.
        for _ in exp_backoff(num_tries=3):
            try:
                configure_kubectl(layer)
                break
            except Exception as err:
                logger.exception(str(err))
                logger.info("Retrying attempt to talk to K8s cluster...")
        else:
            raise Exception("Couldn't connect to the K8s cluster")

        load_kube_config()
        self.v1 = CoreV1Api()
        super(DatadogProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        namespaces = self.v1.list_namespace(
            field_selector=f"metadata.name={self.layer.name}"
        )
        if len(namespaces.items) == 0:
            self.v1.create_namespace(
                body=V1Namespace(metadata=V1ObjectMeta(name=self.layer.name))
            )
        try:
            secret = self.v1.read_namespaced_secret("secret", self.layer.name)
            if (
                "DATADOG_API_KEY" not in secret.data
                or secret.data["DATADOG_API_KEY"] == ""
            ):
                api_key = self.create_secret()
            else:
                api_key = base64.b64decode(secret.data["DATADOG_API_KEY"]).decode("utf-8")
        except ApiException:
            self.v1.create_namespaced_secret(
                namespace=self.layer.name,
                body=V1Secret(
                    metadata=V1ObjectMeta(name="secret"),
                    string_data={"DATADOG_API_KEY": ""},
                ),
            )
            api_key = self.create_secret()
        self.module.data["api_key"] = api_key
        super(DatadogProcessor, self).process(module_idx)

    def create_secret(self) -> str:
        value = self.module.data.get("api_key") or click.prompt(
            "Please enter your datadog api key (from https://app.datadoghq.com/account/settings#api)",
            type=click.STRING,
        )

        if not self.validate_api_key(value):
            raise UserErrors(
                "The api key which you passed was invalid, please provide a valid api key from "
                "https://app.datadoghq.com/account/settings#api"
            )

        secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
        patch = [
            {"op": "replace", "path": "/data/DATADOG_API_KEY", "value": secret_value}
        ]
        self.v1.patch_namespaced_secret("secret", self.layer.name, patch)
        return value

    def validate_api_key(self, api_key: str) -> bool:
        response = get(
            "https://api.datadoghq.com/api/v1/validate",
            headers={"Content-Type": "application/json", "DD-API-KEY": api_key},
        )
        return response.status_code == codes.ok
