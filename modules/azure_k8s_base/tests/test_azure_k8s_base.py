# type: ignore
import os

from pytest_mock import MockFixture

from modules.azure_k8s_base.azure_k8s_base import AzureK8sBaseProcessor
from opta.layer import Layer


class TestAzureK8sBaseProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(),
                "tests",
                "fixtures",
                "dummy_data",
                "azure_dummy_config_parent.yaml",
            ),
            None,
        )
        idx = len(layer.modules)
        k8s_base_module = layer.get_module_by_type("azure-k8s-base", idx)[0]
        mocked_process = mocker.patch(
            "modules.azure_k8s_base.azure_k8s_base.ModuleProcessor.process"
        )
        AzureK8sBaseProcessor(k8s_base_module, layer).process(idx)
        mocked_process.assert_called_once_with(idx)
