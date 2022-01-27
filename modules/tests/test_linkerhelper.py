# type: ignore
import os

from pytest_mock import MockFixture

from modules.linker_helper import LinkerHelper
from opta.layer import Layer


class TestLinkerHelper:
    def test_handle_link(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "local_dummy_config.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        atlas_module = layer.get_module("mongodbatlas", idx)

        atlas_module.data["link_secrets"] = []
        app_module.data["link_secrets"] = []
        link_permissions = []
        for link_data in app_module.data.get("links", []):
            if type(link_data) is str:
                link_permissions = []
            elif type(link_data) is dict:
                link_permissions = list(link_data.values())[0]
        print(link_permissions)
        LinkerHelper.handle_link(
            app_module,
            atlas_module,
            link_permissions,
            required_vars=["db_password", "db_user", "mongodb_atlas_connection_string"],
        )
        link_secret_keys = [x["name"] for x in app_module.data["link_secrets"]]
        assert "DB_USER" in link_secret_keys
