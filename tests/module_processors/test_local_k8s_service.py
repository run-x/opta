# type: ignore
import os

from pytest_mock import MockFixture

from opta.layer import Layer
from opta.module_processors.local_k8s_service import LocalK8sServiceProcessor


class TestLocalK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "local_dummy_config.yaml",
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        mocked_process = mocker.patch(
            "opta.module_processors.local_k8s_service.LocalK8sModuleProcessor.process"
        )
        LocalK8sServiceProcessor(app_module, layer).process(idx)
        mocked_process.assert_called_once_with(idx)
        assert app_module.data["env_vars"] == [{"name": "A", "value": "B"}]
        assert app_module.data["link_secrets"] == [
            {"name": "database_db_user", "value": "${{module.database.db_user}}"},
            {"name": "database_db_name", "value": "${{module.database.db_name}}"},
            {"name": "database_db_password", "value": "${{module.database.db_password}}"},
            {"name": "database_db_host", "value": "${{module.database.db_host}}"},
            {"name": "redis_cache_host", "value": "${{module.redis.cache_host}}"},
            # {
            #     "name": "redis_cache_auth_token",
            #     "value": "${{module.redis.cache_auth_token}}",
            # },
            {"name": "DBUSER2", "value": "${{module.database2.db_user}}"},
            {"name": "DBNAME2", "value": "${{module.database2.db_name}}"},
            {"name": "BLAH", "value": "${{module.database2.db_password}}"},
            {"name": "DBHOST2", "value": "${{module.database2.db_host}}"},
            {"name": "CACHEHOST2", "value": "${{module.redis2.cache_host}}"},
        ]
        assert app_module.data["manual_secrets"] == [
            "BALONEY",
        ]
