# type: ignore

import os

import pytest
from pytest_mock import MockFixture
from requests import Response, codes

from opta.amplitude import AmplitudeClient
from opta.constants import OPTA_DISABLE_REPORTING


@pytest.mark.usefixtures("hide_debug_mode")
class TestAmplitudeClient:
    def test_send_event(self, mocker: MockFixture):
        mocker.patch("opta.amplitude.VERSION")
        mocked_post = mocker.patch("opta.amplitude.post")
        mocked_response = mocker.Mock(spec=Response)
        mocked_response.status_code = codes.ok
        mocked_post.return_value = mocked_response
        client = AmplitudeClient()

        client.send_event(client.APPLY_EVENT)
        mocked_post.assert_called_once_with(
            "https://api2.amplitude.com/2/httpapi",
            params={},
            headers={"Content-Type": "application/json", "Accept": "*/*"},
            json=mocker.ANY,
        )

    def test_dont_send_event(self, mocker: MockFixture):
        mocked_post = mocker.patch("opta.amplitude.post")
        mocked_response = mocker.Mock(spec=Response)
        mocked_response.status_code = codes.ok
        mocked_post.return_value = mocked_response
        client = AmplitudeClient()
        os.environ[OPTA_DISABLE_REPORTING] = "1"

        client.send_event(client.APPLY_EVENT)
        mocked_post.assert_not_called()
