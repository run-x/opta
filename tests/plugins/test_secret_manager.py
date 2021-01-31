# type: ignore
import os

import pytest
from pytest_mock import MockFixture, mocker  # noqa

from opta.plugins.secret_manager import get_module


class TestSecretManager:
    def test_get_module_no_kubectl(self, mocker: MockFixture):  # noqa
        mocked_is_tool = mocker.patch("opta.plugins.secret_manager.is_tool")
        mocked_is_tool.return_value = False
        with pytest.raises(Exception):
            get_module("a", "b", "c", "d")
        mocked_is_tool.assert_called_once_with("kubectl")

    def test_get_module_no_configfile(self, mocker: MockFixture):  # noqa
        mocked_is_tool = mocker.patch("opta.plugins.secret_manager.is_tool")
        mocked_is_tool.return_value = True
        mocked_path_exists = mocker.patch("os.path.exists")
        mocked_path_exists.return_value = False
        with pytest.raises(Exception):
            get_module("a", "b", "c", "d")
        mocked_is_tool.assert_called_once_with("kubectl")
        mocked_path_exists.assert_called_once_with("d")

    def test_get_module_all_good(self):

        target_module = get_module(
            "app",
            "BALONEY",
            "dummy-env",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "plugins",
                "dummy_config1.yaml",
            ),
        )

        assert target_module.key == "app"

    def test_get_module_no_secret(self):
        with pytest.raises(Exception) as excinfo:
            get_module(
                "app",
                "BALONEY",
                "dummy-env",
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "plugins",
                    "dummy_config2.yaml",
                ),
            )
            assert "Secret not found" in str(excinfo.value)
