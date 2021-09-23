import pytest
import requests
import requests_mock
from pytest_mock import MockFixture

from opta.upgrade import (
    LATEST_VERSION_FILE_URL,
    UPGRADE_INSTRUCTIONS_URL,
    _get_latest_version,
    check_version_upgrade,
)

TEST_LATEST_VERSION = "1.11.1"
TEST_OLD_VERSION = "1.9.6"


class TestGetLatestVersion:
    def test_returns_version_number_from_file(self) -> None:
        with requests_mock.Mocker() as m:
            m.register_uri(
                "GET", LATEST_VERSION_FILE_URL, text=f"{TEST_LATEST_VERSION}\n"
            )
            assert _get_latest_version() == TEST_LATEST_VERSION

    def test_raises_exception_if_connection_error(self) -> None:
        with requests_mock.Mocker() as m:
            m.register_uri(
                "GET", LATEST_VERSION_FILE_URL, exc=requests.exceptions.ConnectTimeout
            )
            with pytest.raises(Exception):
                _get_latest_version()

    def test_raises_exception_if_error_response(self) -> None:
        with requests_mock.Mocker() as m:
            m.register_uri(
                "GET", LATEST_VERSION_FILE_URL, status_code=404, text="Not Found"
            )
            with pytest.raises(Exception):
                _get_latest_version()

            m.register_uri(
                "GET", LATEST_VERSION_FILE_URL, status_code=500, text="Server error"
            )
            with pytest.raises(Exception):
                _get_latest_version()


class TestCheckVersionUpgrade:
    def test_does_not_check_if_should_check_false(self, mocker: MockFixture) -> None:
        mocked_should_check = mocker.patch(
            "opta.upgrade._should_check_for_version_upgrade", return_value=False
        )
        mocked_get_latest_version = mocker.patch("opta.upgrade._get_latest_version")
        check_version_upgrade()
        mocked_should_check.assert_called_once()
        mocked_get_latest_version.assert_not_called()

    def test_logs_update_instructions_if_newer_version_available(
        self, mocker: MockFixture
    ) -> None:
        mocker.patch(
            "opta.upgrade._should_check_for_version_upgrade", return_value=True
        )
        mocker.patch(
            "opta.upgrade._get_latest_version", return_value=TEST_LATEST_VERSION
        )
        mocker.patch("opta.upgrade.VERSION", TEST_OLD_VERSION)
        mocked_logger_warning = mocker.patch("opta.upgrade.logger.warning")
        check_version_upgrade()
        mocked_logger_warning.assert_called_once()
        warning_message: str = mocked_logger_warning.call_args.args[0]
        assert warning_message.find(TEST_OLD_VERSION) > -1
        assert warning_message.find(TEST_LATEST_VERSION) > -1
        assert warning_message.find(UPGRADE_INSTRUCTIONS_URL) > -1

    def test_handles_get_latest_version_exceptions(self, mocker: MockFixture) -> None:
        mocker.patch(
            "opta.upgrade._should_check_for_version_upgrade", return_value=True
        )
        mocked_get_latest_version = mocker.patch(
            "opta.upgrade._get_latest_version",
            side_effect=requests.exceptions.ConnectTimeout,
        )
        check_version_upgrade()
        mocked_get_latest_version.assert_called_once()
