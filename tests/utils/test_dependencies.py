from typing import Generator

import pytest
from pytest_mock import MockFixture

from opta.exceptions import UserErrors
from opta.utils import dependencies


class TestDependencies:
    def test_get_missing_path_executables(self, mocker: MockFixture) -> None:
        mock_is_tool = mocker.patch("opta.utils.dependencies.is_tool")
        mock_is_tool.return_value = False
        dependencies.register_path_executable("foo")

        missing = dependencies.get_missing_path_executables({"foo"})

        mock_is_tool.assert_called_once_with("foo")
        assert missing == {"foo": None}

    def test_get_missing_path_executables_none(self, mocker: MockFixture) -> None:
        mock_is_tool = mocker.patch("opta.utils.dependencies.is_tool")
        mock_is_tool.return_value = True
        dependencies.register_path_executable("foo")

        missing = dependencies.get_missing_path_executables({"foo"})

        mock_is_tool.assert_called_once_with("foo")
        assert missing == {}

    def test_get_missing_path_executables_unregistered(self, mocker: MockFixture) -> None:
        mock_is_tool = mocker.patch("opta.utils.dependencies.is_tool", return_value=True)

        with pytest.raises(ValueError) as e:
            dependencies.get_missing_path_executables({"foo"})

        assert str(e.value) == "foo is not a registered path executable"
        mock_is_tool.assert_not_called()

    def test_register_path_executable_new(self) -> None:
        dependencies.register_path_executable("foo")
        dependencies.register_path_executable("bar")
        assert dependencies._registered_path_executables == {"foo": None, "bar": None}

    def test_register_path_executable_new_with_url(self) -> None:
        dependencies.register_path_executable("foo", install_url="bar")
        assert dependencies._registered_path_executables == {"foo": "bar"}

    def test_register_path_executable_duplicate(self) -> None:
        dependencies.register_path_executable("foo")

        with pytest.raises(ValueError) as e:
            dependencies.register_path_executable("foo")

        assert str(e.value) == "foo already registered as a path executable"

    def test_validate_installed_path_executables(self, mocker: MockFixture) -> None:
        mocker.patch(
            "opta.utils.dependencies.get_missing_path_executables",
            return_value={"foo": "bar", "spam": None},
        )

        with pytest.raises(UserErrors) as e:
            dependencies.validate_installed_path_executables(frozenset({"foo", "spam"}))

        assert (
            str(e.value)
            == "Missing required executables on PATH: foo (visit bar to install); spam"
        )

    def test_validate_installed_path_executables_none(self, mocker: MockFixture) -> None:
        mock_get_missing = mocker.patch(
            "opta.utils.dependencies.get_missing_path_executables", return_value={}
        )
        mock_sorted = mocker.patch("opta.utils.dependencies.sorted")

        dependencies.validate_installed_path_executables(frozenset({"foo"}))

        mock_get_missing.assert_called_once_with(frozenset({"foo"}))
        mock_sorted.assert_not_called()

    @pytest.fixture(autouse=True)
    def registered_paths(self) -> Generator:
        old = dependencies._registered_path_executables
        dependencies._registered_path_executables = {}

        yield

        dependencies._registered_path_executables = old
