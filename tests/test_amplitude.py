# type: ignore

import os
import sys

from pytest_mock import MockFixture, mocker  # noqa
from requests import Response, codes

from opta.amplitude import AmplitudeClient
from opta.constants import OPTA_DISABLE_REPORTING


class TestAmplitudeClient:
    def test_send_event(self, mocker: MockFixture):  # noqa
        mocked_version = mocker.patch("opta.amplitude.VERSION")
        mocked_post = mocker.patch("opta.amplitude.post")
        mocked_response = mocker.Mock(spec=Response)
        mocked_response.status_code = codes.ok
        mocked_post.return_value = mocked_response
        client = AmplitudeClient()
        del sys._called_from_test
        try:
            client.send_event(client.APPLY_EVENT)
            mocked_post.assert_called_once_with(
                "https://api2.amplitude.com/2/httpapi",
                params={},
                headers={"Content-Type": "application/json", "Accept": "*/*"},
                json=mocker.ANY,
            )
        finally:
            sys._called_from_test = True

    def test_dont_send_event(self, mocker: MockFixture):  # noqa
        mocked_post = mocker.patch("opta.amplitude.post")
        mocked_response = mocker.Mock(spec=Response)
        mocked_response.status_code = codes.ok
        mocked_post.return_value = mocked_response
        client = AmplitudeClient()
        del sys._called_from_test
        os.environ[OPTA_DISABLE_REPORTING] = "1"
        try:
            client.send_event(client.APPLY_EVENT)
            mocked_post.assert_not_called()
        finally:
            sys._called_from_test = True
            del os.environ[OPTA_DISABLE_REPORTING]
