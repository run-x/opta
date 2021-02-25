# type: ignore
import json
import time
from logging import LogRecord

from pytest_mock import MockFixture, mocker  # noqa
from requests import Response, codes

from opta.datadog_logging import CLIENT_TOKEN, DEFAULT_CACHE_SIZE, DatadogLogHandler


class TestDatadogLogHandler:
    def test_emit(self, mocker: MockFixture):  # noqa
        mocked_record = mocker.Mock(spec=LogRecord)
        mocked_cache_entry = mocker.Mock()
        mocked_transform_record = mocker.patch(
            "opta.datadog_logging.DatadogLogHandler.transform_record",
            return_value=mocked_cache_entry,
        )
        mocked_flush = mocker.patch("opta.datadog_logging.DatadogLogHandler.flush")
        handler = DatadogLogHandler()
        handler.emit(mocked_record)
        assert handler.cache == [mocked_cache_entry]
        mocked_flush.assert_not_called()
        mocked_transform_record.assert_called_once_with(mocked_record)

    def test_emit_with_flush(self, mocker: MockFixture):  # noqa
        mocked_record = mocker.Mock(spec=LogRecord)
        mocked_cache_entry = mocker.Mock()
        mocked_transform_record = mocker.patch(
            "opta.datadog_logging.DatadogLogHandler.transform_record",
            return_value=mocked_cache_entry,
        )
        mocked_flush = mocker.patch("opta.datadog_logging.DatadogLogHandler.flush")
        handler = DatadogLogHandler()
        handler.cache = [mocker.Mock() for _ in range(DEFAULT_CACHE_SIZE)]
        handler.emit(mocked_record)
        assert handler.cache[-1] == mocked_cache_entry
        assert len(handler.cache) == DEFAULT_CACHE_SIZE + 1
        mocked_flush.assert_called_once_with()
        mocked_transform_record.assert_called_once_with(mocked_record)

    def test_flush(self, mocker: MockFixture):  # noqa
        mocked_response = mocker.Mock(spec=Response)
        mocked_response.status_code = codes.ok
        mocked_post = mocker.patch(
            "opta.datadog_logging.post", return_value=mocked_response
        )
        handler = DatadogLogHandler()
        cache_entry = {
            "date": int(time.time() * 1000),
            "message": "blah",
            "status": "INFO",
        }
        handler.cache = [cache_entry]
        handler.flush()
        assert handler.cache == []
        mocked_post.assert_called_once_with(
            url=f"https://browser-http-intake.logs.datadoghq.com/v1/input/{CLIENT_TOKEN}",
            params=mocker.ANY,
            headers={
                "authority": "browser-http-intake.logs.datadoghq.com",
                "content-type": "text/plain;charset=UTF-8",
                "accept": "*/*",
            },
            data=json.dumps(cache_entry).encode("utf-8"),
            timeout=5,
        )
