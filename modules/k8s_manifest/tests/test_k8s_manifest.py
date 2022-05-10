import os

from modules.k8s_manifest.k8s_manifest import K8smanifestProcessor
from opta.layer import Layer


class TestK8smanifestProcessor:
    def test_local(self) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "local_dummy_config.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        k8smanifest_module = layer.get_module("k8smanifest", idx)
        K8smanifestProcessor(k8smanifest_module, layer).process(idx)
        assert k8smanifest_module.data["kubeconfig"] == "~/.kube/config"  # type: ignore
        assert k8smanifest_module.data["kubecontext"] == "kind-opta-local-cluster"  # type: ignore
