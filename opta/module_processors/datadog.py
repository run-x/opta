import base64
from typing import TYPE_CHECKING

import click
from kubernetes.client import ApiException, CoreV1Api, V1Namespace, V1ObjectMeta, V1Secret
from kubernetes.config import load_kube_config

from opta.core.kubernetes import configure_kubectl
from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class DatadogProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "datadog":
            raise Exception(
                f"The module {module.name} was expected to be of type datadog"
            )
        configure_kubectl(layer)
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
            if "DATADOG_API_KEY" not in secret.data:
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
        value = click.prompt("Please enter your datadog api key", type=str)
        secret_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
        patch = [
            {"op": "replace", "path": "/data/DATADOG_API_KEY", "value": secret_value}
        ]
        self.v1.patch_namespaced_secret("secret", self.layer.name, patch)
        return value
