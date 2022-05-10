from typing import TYPE_CHECKING

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

import os


class K8smanifestProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-manifest":
            raise Exception(
                f"The module {module.name} was expected to be of type k8s-manifest"
            )
        super(K8smanifestProcessor, self).__init__(module, layer)

    def get_k8s_module_source(self, module_idx: int) -> str:
        k8s_cluster_modules = self.layer.get_module_by_type("k8s-cluster", module_idx)
        cluster_from_parent = False
        if len(k8s_cluster_modules) == 0 and self.layer.parent is not None:
            k8s_cluster_modules = self.layer.parent.get_module_by_type("k8s-cluster")
            cluster_from_parent = True

        if len(k8s_cluster_modules) == 0:
            raise UserErrors(
                "Could not find k8s-cluster module installed in this environment"
            )
        k8s_cluster_module = k8s_cluster_modules[0]
        return (
            "data.terraform_remote_state.parent.outputs"
            if cluster_from_parent
            else f"module.{k8s_cluster_module.name}"
        )

    def __handle_aws(self, module_idx: int) -> None:
        module_source = self.get_k8s_module_source(module_idx)
        self.module.data["host"] = f"${{{{{module_source}.k8s_endpoint}}}}"
        self.module.data["token"] = "${{data.aws_eks_cluster_auth.k8s.token}}"
        self.module.data[
            "cluster_ca_certificate"
        ] = f"${{{{base64decode({module_source}.k8s_ca_data)}}}}"

    def __handle_gcp(self, module_idx: int) -> None:
        module_source = self.get_k8s_module_source(module_idx)
        self.module.data[
            "host"
        ] = "https://${{data.google_container_cluster.k8s.endpoint}}"
        self.module.data["token"] = "{k8s_access_token}"
        self.module.data[
            "cluster_ca_certificate"
        ] = f"${{{{base64decode({module_source}.k8s_ca_data)}}}}"

    def __handle_azure(self, module_idx: int) -> None:
        module_source = self.get_k8s_module_source(module_idx)
        self.module.data["host"] = f"${{{{{module_source}.k8s_endpoint}}}}"
        self.module.data[
            "client_certificate"
        ] = f"${{{{base64decode({module_source}.client_cert)}}}}"
        self.module.data[
            "client_key"
        ] = f"${{{{base64decode({module_source}.client_key)}}}}"
        self.module.data[
            "cluster_ca_certificate"
        ] = f"${{{{base64decode({module_source}.k8s_ca_data)}}}}"

    def __handle_local(self, module_idx: int) -> None:
        self.module.data["kubeconfig"] = "~/.kube/config"
        self.module.data["kubecontext"] = "kind-opta-local-cluster"

    def process(self, module_idx: int) -> None:
        file_path: str = self.module.data.get("file_path")
        if not file_path.startswith("/"):
            file_path = os.path.join(os.path.dirname(self.layer.path), file_path)
        self.module.data["file_path"] = file_path

        if self.layer.cloud == "aws":
            self.__handle_aws(module_idx)
        elif self.layer.cloud == "google":
            self.__handle_gcp(module_idx)
        elif self.layer.cloud == "azurerm":
            self.__handle_azure(module_idx)
        elif self.layer.cloud == "local":
            self.__handle_local(module_idx)
        super(K8smanifestProcessor, self).process(module_idx)
