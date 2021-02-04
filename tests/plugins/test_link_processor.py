# type: ignore
import os

from opta.layer import Layer
from opta.plugins.link_processor import LinkProcessor


class TestLinkProcessor:
    def test_with_link(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "plugins",
                "dummy_config1.yaml",
            ),
            "dummy-env",
        )
        current_modules = layer.blocks[0].modules
        LinkProcessor().process(current_modules)
        for module in current_modules:
            if module.key == "app":
                assert module.data["env_vars"] == [
                    {"name": "APPENV", "value": "{env}"},
                    {"name": "database_db_user", "value": "${{module.database.db_user}}"},
                    {
                        "name": "database_db_password",
                        "value": "${{module.database.db_password}}",
                    },
                    {"name": "database_db_host", "value": "${{module.database.db_host}}"},
                    {"name": "database_db_name", "value": "${{module.database.db_name}}"},
                ]

    def test_with_new_link(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "plugins",
                "dummy_config3.yaml",
            ),
            "dummy-env",
        )
        current_modules = layer.blocks[0].modules
        LinkProcessor().process(current_modules)
        for module in current_modules:
            if module.key == "app":
                assert module.data["env_vars"] == [
                    {"name": "APPENV", "value": "{env}"},
                    {"name": "database_db_user", "value": "${{module.database.db_user}}"},
                    {
                        "name": "database_db_password",
                        "value": "${{module.database.db_password}}",
                    },
                    {"name": "database_db_host", "value": "${{module.database.db_host}}"},
                    {"name": "database_db_name", "value": "${{module.database.db_name}}"},
                ]

    def test_without_link(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "plugins",
                "dummy_config2.yaml",
            ),
            "dummy-env",
        )
        current_modules = layer.blocks[0].modules
        LinkProcessor().process(current_modules)
        for module in current_modules:
            if module.key == "app":
                assert module.data["env_vars"] == [
                    {"name": "APPENV", "value": "{env}"},
                ]
