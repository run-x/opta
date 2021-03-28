# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from opta.layer import Layer
from opta.module_processors.gcp_k8s_service import GcpK8sServiceProcessor


class TestGCPK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "gcp_dummy_config.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 6)
        mocked_process = mocker.patch(
            "opta.module_processors.gcp_k8s_service.GcpK8sModuleProcessor.process"
        )
        GcpK8sServiceProcessor(app_module, layer).process(5)
        mocked_process.assert_called_once_with(5)
        assert app_module.data["secrets"] == [
            {"name": "BALONEY", "value": ""},
            {"name": "database_db_user", "value": "${{module.database.db_user}}"},
            {"name": "database_db_name", "value": "${{module.database.db_name}}"},
            {"name": "database_db_password", "value": "${{module.database.db_password}}"},
            {"name": "database_db_host", "value": "${{module.database.db_host}}"},
            {"name": "redis_cache_host", "value": "${{module.redis.cache_host}}"},
            {
                "name": "redis_cache_auth_token",
                "value": "${{module.redis.cache_auth_token}}",
            },
        ]
        assert app_module.data["read_buckets"] == ["${{module.bucket1.bucket_name}}"]
        assert app_module.data["write_buckets"] == [
            "${{module.bucket2.bucket_name}}",
            "${{module.bucket3.bucket_name}}",
        ]

    def test_bad_postgres_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "gcp_dummy_config.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 6)
        app_module.data["links"] = []
        app_module.data["links"].append({"database": "read"})
        with pytest.raises(Exception):
            GcpK8sServiceProcessor(app_module, layer).process(5)

    def test_bad_redis_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "gcp_dummy_config.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 6)
        app_module.data["links"] = []
        app_module.data["links"].append({"redis": "read"})
        with pytest.raises(Exception):
            GcpK8sServiceProcessor(app_module, layer).process(5)

    def test_bad_gcs_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "gcp_dummy_config.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 6)
        app_module.data["links"] = []
        app_module.data["links"].append({"bucket1": "blah"})
        with pytest.raises(Exception):
            GcpK8sServiceProcessor(app_module, layer).process(6)
