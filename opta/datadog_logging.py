import os
import platform
import time
from logging import NOTSET, Handler, LogRecord, getLogger
from typing import Any, Dict, List

from getmac import get_mac_address
from git.config import GitConfigParser
from requests import codes, post

from opta.constants import DEV_VERSION, OPTA_DISABLE_REPORTING, SESSION_ID, VERSION
from opta.utils import json

CLIENT_TOKEN = "pub40d867605951d2a30fb8020e193ee7e5"  # nosec
DEFAULT_CACHE_SIZE = 10
logger = getLogger("opta")


class DatadogLogHandler(Handler):
    def __init__(self, level: int = NOTSET, cache_size: int = DEFAULT_CACHE_SIZE):
        self.cache: List[Dict[str, Any]] = []
        self.cache_size = cache_size
        self.user_id = GitConfigParser().get_value("user", "email", "no_user")
        self.device_id = get_mac_address()
        self.os_name = os.name
        self.platform = platform.system()
        self.os_version = platform.version()
        super(DatadogLogHandler, self).__init__(level)

    def transform_record(self, record: LogRecord) -> Dict[str, Any]:
        msg = self.format(record)
        return {
            "date": int(time.time() * 1000),
            "message": msg,
            "status": record.levelname,
        }

    def emit(self, record: LogRecord) -> None:
        self.cache.append(self.transform_record(record))
        if len(self.cache) >= DEFAULT_CACHE_SIZE:
            self.flush()

    def flush(self) -> None:
        env = "dev" if VERSION in ["", DEV_VERSION] else "production"
        if self.cache:
            parameters = {
                "ddsource": "cli",
                "ddtags": f"env:{env},version:{VERSION or 'dev'}",
                "user_id": self.user_id,
                "device_id": self.device_id,
                "os_name": self.os_name,
                "platform": self.platform,
                "os_version": self.os_version,
                "session_id": SESSION_ID,
            }
            headers = {
                "authority": "browser-http-intake.logs.datadoghq.com",
                "content-type": "text/plain;charset=UTF-8",
                "accept": "*/*",
            }

            if (
                os.environ.get(OPTA_DISABLE_REPORTING) is not None
                or VERSION == DEV_VERSION
            ):
                self.cache = []
                return

            try:
                response = post(
                    url=f"https://browser-http-intake.logs.datadoghq.com/v1/input/{CLIENT_TOKEN}",
                    params=parameters,
                    headers=headers,
                    data="\n".join(map(lambda x: json.dumps(x), self.cache)).encode(
                        "utf-8"
                    ),
                    timeout=5,
                )
                if response.status_code != codes.ok:
                    return
                else:
                    self.cache = []
            except Exception as err:
                logger.debug(
                    f"Unexpected error when connecting to datadog: {err=}, {type(err)=}"
                )

    def close(self) -> None:
        self.acquire()
        try:
            self.flush()
        finally:
            self.release()
