# type: ignore
import os

from pytest_mock import MockFixture

from opta.layer import Layer
from modules.local_k8s_service.local_k8s_service import LocalK8sServiceProcessor


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
            "modules.local_k8s_service.LocalK8sModuleProcessor.process"
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
            {"name": "mongodb_db_user", "value": "${{module.mongodb.db_user}}"},
            {"name": "mongodb_db_name", "value": "${{module.mongodb.db_name}}"},
            {"name": "mongodb_db_password", "value": "${{module.mongodb.db_password}}"},
            {"name": "mongodb_db_host", "value": "${{module.mongodb.db_host}}"},
            {"name": "mysql_db_user", "value": "${{module.mysql.db_user}}"},
            {"name": "mysql_db_name", "value": "${{module.mysql.db_name}}"},
            {"name": "mysql_db_password", "value": "${{module.mysql.db_password}}"},
            {"name": "mysql_db_host", "value": "${{module.mysql.db_host}}"},
            {"name": "DBUSER2", "value": "${{module.database2.db_user}}"},
            {"name": "DBNAME2", "value": "${{module.database2.db_name}}"},
            {"name": "BLAH", "value": "${{module.database2.db_password}}"},
            {"name": "DBHOST2", "value": "${{module.database2.db_host}}"},
            {"name": "CACHEHOST2", "value": "${{module.redis2.cache_host}}"},
            {"name": "DB_PASSWORD", "value": "${{module.mongodbatlas.db_password}}"},
            {"name": "DB_USER", "value": "${{module.mongodbatlas.db_user}}"},
            {
                "name": "MONGODB_URI",
                "value": "${{module.mongodbatlas.mongodb_atlas_connection_string}}",
            },
        ]
        assert app_module.data["manual_secrets"] == [
            "BALONEY",
        ]

    def test_handle_pg_link(self, mocker: MockFixture):
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
        pg_module = layer.get_module("database2", idx)

        pg_module.data["link_secrets"] = []
        pg_module.data["manual_secrets"] = []
        app_module.data["link_secrets"] = []
        app_module.data["manual_secrets"] = []
        link_permissions = []
        for link_data in pg_module.data.get("links", []):
            if type(link_data) is str:
                link_permissions = []
            elif type(link_data) is dict:
                link_permissions = list(link_data.values())[0]
        lp = LocalK8sServiceProcessor(app_module, layer)
        lp.handle_pg_link(pg_module, link_permissions)
        link_secret_keys = [x["name"] for x in app_module.data["link_secrets"]]
        assert "database2_db_user" in link_secret_keys

    def test_handle_redis_link(self, mocker: MockFixture):
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
        redis_module = layer.get_module("redis", idx)

        redis_module.data["link_secrets"] = []
        redis_module.data["manual_secrets"] = []
        app_module.data["link_secrets"] = []
        app_module.data["manual_secrets"] = []
        link_permissions = []
        for link_data in redis_module.data.get("links", []):
            if type(link_data) is str:
                link_permissions = []
            elif type(link_data) is dict:
                link_permissions = list(link_data.values())[0]
        lp = LocalK8sServiceProcessor(app_module, layer)
        lp.handle_redis_link(redis_module, link_permissions)
        link_secret_keys = [x["name"] for x in app_module.data["link_secrets"]]
        assert "redis_cache_host" in link_secret_keys

    def test_handle_mysql_link(self, mocker: MockFixture):
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
        mysql_module = layer.get_module("mysql", idx)

        mysql_module.data["link_secrets"] = []
        mysql_module.data["manual_secrets"] = []
        app_module.data["link_secrets"] = []
        app_module.data["manual_secrets"] = []
        link_permissions = []
        for link_data in mysql_module.data.get("links", []):
            if type(link_data) is str:
                link_permissions = []
            elif type(link_data) is dict:
                link_permissions = list(link_data.values())[0]
        lp = LocalK8sServiceProcessor(app_module, layer)
        lp.handle_mysql_link(mysql_module, link_permissions)
        link_secret_keys = [x["name"] for x in app_module.data["link_secrets"]]
        assert "mysql_db_user" in link_secret_keys

    def test_handle_mongodb_link(self, mocker: MockFixture):
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
        mongodb_module = layer.get_module("mongodb", idx)

        mongodb_module.data["link_secrets"] = []
        mongodb_module.data["manual_secrets"] = []
        app_module.data["link_secrets"] = []
        app_module.data["manual_secrets"] = []
        link_permissions = []
        for link_data in mongodb_module.data.get("links", []):
            if type(link_data) is str:
                link_permissions = []
            elif type(link_data) is dict:
                link_permissions = list(link_data.values())[0]
        lp = LocalK8sServiceProcessor(app_module, layer)
        lp.handle_mongodb_link(mongodb_module, link_permissions)
        link_secret_keys = [x["name"] for x in app_module.data["link_secrets"]]
        assert "mongodb_db_user" in link_secret_keys
