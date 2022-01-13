import pytest
import os
from opta.layer import Layer
from modules.k8s_resource.k8s_resource import K8sresourceProcessor
from pytest_mock import MockFixture
import tempfile
class TestK8sresourceProcessor:
    def test_local_getconfig(self) -> None:
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "local_dummy_config.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        k8sresource_module = layer.get_module("k8sresource", idx)
        K8sresourceProcessor(k8sresource_module, layer)
        assert(k8sresource_module.data["kubeconfig"] == "~/.kube/config")
        assert(k8sresource_module.data["kubecontext"] == "kind-opta-local-cluster")
        
    
 