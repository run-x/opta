import os
import platform
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Tuple

import requests
from getmac import get_mac_address
from git.config import GitConfigParser

from opta.constants import VERSION
from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module

if os.environ.get("OPTA_STAGING"):
    OPTA_DOMAIN = "api.staging.runx.dev"
else:
    OPTA_DOMAIN = "api.app.runx.dev"


class RunxProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "runx":
            raise Exception(f"The module {module.name} was expected to be of type runx")
        if os.environ.get("OPTA_API_KEY") is None:
            raise UserErrors("Need opta api key present for this to run")
        self.api_key = os.environ.get("OPTA_API_KEY")
        self.user_id = GitConfigParser().get_value("user", "email", "no_user")
        self.device_id = get_mac_address()
        self.os_name = os.name
        self.platform = platform.system()
        self.os_version = platform.version()
        super(RunxProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        self.fetch_jwt()

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        validation_data, jwt = self.fetch_jwt()
        is_environment = self.layer.parent is None
        url_path = "/config/environments" if is_environment else "/config/services"
        body = {
            "org_id": validation_data["org_id"],
            "name": self.layer.name,
            "opta_version": VERSION,
            "status": "SUCCESS" if exception is None else "FAILURE",
            "spec": self.layer.original_spec,
            "metadata": {
                "user_id": self.user_id,
                "device_id": self.device_id,
                "os_name": self.os_name,
                "platform": self.platform,
                "os_version": self.os_version,
                "active_variables": self.layer.variables,
                "module_idx": module_idx,
            },
            "time": datetime.utcnow().isoformat(),
        }
        if not is_environment:
            body["environment_name"] = self.layer.parent.name  # type: ignore
        logger.info("Sending layer deployment data over to opta backend")
        resp = requests.post(
            f"https://{OPTA_DOMAIN}{url_path}", json=body, headers={"opta": jwt}
        )
        if resp.status_code != 201:
            raise Exception(
                f"Invalid response when attempting to send data to backend: {resp.json()}"
            )

    def fetch_jwt(self) -> Tuple[dict, str]:
        resp = requests.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": self.api_key}
        )
        if resp.status_code == 404:
            raise UserErrors(
                f"Looks like it was an invalid api key: {resp.json()['message']}"
            )
        if resp.status_code != 200:
            raise Exception(
                f"Invalid response when attempting to validate the api token: {resp.json()}"
            )
        jwt = resp.headers.get("opta")
        if jwt is None:
            raise Exception(f"Got an invalid jwt back: {jwt}")
        return resp.json(), jwt
