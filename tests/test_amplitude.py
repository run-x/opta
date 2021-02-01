# type: ignore

import sys

from pytest_mock import MockFixture, mocker  # noqa
from requests import Response, codes

from opta.amplitude import AmplitudeClient


class TestAmplitudeClient:
    def test_send_event(self, mocker: MockFixture):  # noqa
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
