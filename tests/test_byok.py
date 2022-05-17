# type: ignore
import os

from modules.local_k8s_service.local_k8s_service import LocalK8sServiceProcessor
from opta.layer import Layer


class TestByok:
    def test_all_good(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(),
                "tests",
                "fixtures",
                "sample_opta_files",
                "byok_service.yaml",
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("hello", idx)
        LocalK8sServiceProcessor(app_module, layer).process(idx)

        assert app_module.data["type"] == "k8s-service"
        assert app_module.data["name"] == "hello"
        assert app_module.data["image"] == "ghcr.io/run-x/hello-opta/hello-opta:main"
        assert app_module.data["public_uri"] == ["all/hello"]
        assert app_module.data["env_name"] == "hello"
        assert app_module.data["module_name"] == "hello"

        # check that the helm provider is generated correctly
        assert layer.cloud == "helm"
        assert layer.providers == {
            "helm": {"kubernetes": {"config_path": "{kubeconfig}"}},
            "kubernetes": {"config_path": "{kubeconfig}"},
        }
        os.environ["KUBECONFIG"] = "~/.kube/custom-config"
        gen_provider = layer.gen_providers(0)
        assert gen_provider["provider"] == {
            "helm": {"kubernetes": {"config_path": "~/.kube/config"}},
            "kubernetes": {"config_path": "~/.kube/config"},
        }
        assert gen_provider["terraform"]["required_providers"] == {
            "helm": {"source": "hashicorp/helm", "version": "2.4.1"},
            "kubernetes": {"source": "hashicorp/kubernetes", "version": "2.11.0"},
        }
        assert gen_provider["terraform"]["backend"] == {
            "kubernetes": {
                "config_p" "ath": "~/.kube/config",
                "secret_suffix": "opta-tests-hello",
            },
        }
