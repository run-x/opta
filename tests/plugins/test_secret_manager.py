# type: ignore
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
