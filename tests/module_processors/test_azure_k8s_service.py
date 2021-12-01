# type: ignore
import os

from pytest_mock import MockFixture

from opta.layer import Layer
from modules.azure_k8s_service.azure_k8s_service import AzureK8sServiceProcessor


class TestAzureK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "azure_dummy_config.yaml",
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        mocked_process = mocker.patch(
            "modules.azure_k8s_service.K8sServiceModuleProcessor.process"
        )
        AzureK8sServiceProcessor(app_module, layer).process(idx)
        mocked_process.assert_called_once_with(idx)
        assert app_module.data["env_vars"] == [{"name": "A", "value": "B"}]
        assert app_module.data["link_secrets"] == [
            {"name": "database_db_user", "value": "${{module.database.db_user}}"},
            {"name": "database_db_name", "value": "${{module.database.db_name}}"},
            {"name": "database_db_password", "value": "${{module.database.db_password}}"},
            {"name": "database_db_host", "value": "${{module.database.db_host}}"},
            {"name": "redis_cache_host", "value": "${{module.redis.cache_host}}"},
            {
                "name": "redis_cache_auth_token",
                "value": "${{module.redis.cache_auth_token}}",
            },
            {"name": "DBUSER2", "value": "${{module.database2.db_user}}"},
            {"name": "DBNAME2", "value": "${{module.database2.db_name}}"},
            {"name": "BLAH", "value": "${{module.database2.db_password}}"},
            {"name": "DBHOST2", "value": "${{module.database2.db_host}}"},
            {"name": "CACHEHOST2", "value": "${{module.redis2.cache_host}}"},
            {"name": "CACHEAUTH2", "value": "${{module.redis2.cache_auth_token}}"},
        ]
        assert app_module.data["manual_secrets"] == [
            "BALONEY",
        ]

    def test_prehook(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "azure_dummy_config.yaml",
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        mocked_create_namespace_if_not_exists = mocker.patch(
            "modules.azure_k8s_service.create_namespace_if_not_exists"
        )
        mocked_get_manual_secrets = mocker.patch(
            "modules.azure_k8s_service.get_manual_secrets"
        )
        mocked_get_manual_secrets.return_value = {"BALONEY": "blah"}
        AzureK8sServiceProcessor(app_module, layer).pre_hook(idx)
        mocked_create_namespace_if_not_exists.assert_called_once_with(layer.name)
        mocked_get_manual_secrets.assert_called_once_with(layer.name)
