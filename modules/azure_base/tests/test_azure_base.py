# type: ignore
import os

from pytest_mock import MockFixture

from modules.azure_base.azure_base import AzureBaseProcessor
from opta.layer import Layer


class TestAzureBaseProcessor:
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
        k8s_base_module = layer.get_module_by_type("azure-base", idx)[0]
        mocked_process = mocker.patch(
            "modules.azure_base.azure_base.ModuleProcessor.process"
        )
        AzureBaseProcessor(k8s_base_module, layer).process(idx)
        mocked_process.assert_called_once_with(idx)
        assert k8s_base_module.data["location"] == "centralus"
