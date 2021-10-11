import os
import platform
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Tuple

import boto3
import click
import requests
from botocore.config import Config
from getmac import get_mac_address
from git.config import GitConfigParser
from google.api_core.exceptions import NotFound
from google.cloud import secretmanager
from mypy_boto3_ssm.client import SSMClient

from opta.constants import VERSION
from opta.core.gcp import GCP
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
        self.user_id = GitConfigParser().get_value("user", "email", "no_user")
        self.device_id = get_mac_address()
        self.os_name = os.name
        self.platform = platform.system()
        self.os_version = platform.version()
        super(RunxProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        logger.debug("Checking for runx api key secret")
        current_api_key = self.fetch_secret()
        if current_api_key is None:
            self.set_secret()
        else:
            self.fetch_jwt(current_api_key)

    def fetch_secret(self) -> Optional[str]:
        if self.layer.cloud == "aws":
            return self._fetch_aws_secret()
        elif self.layer.cloud == "google":
            return self._fetch_gcp_secret()
        else:
            raise Exception("Can not handle secrets of type")

    def _fetch_aws_secret(self) -> Optional[str]:
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        ssm_client: SSMClient = boto3.client("ssm", config=Config(region_name=region))
        try:
            parameter = ssm_client.get_parameter(
                Name=f"/opta-{self.layer.get_env()}/runx-api-key", WithDecryption=True
            )
            return parameter["Parameter"]["Value"]
        except ssm_client.exceptions.ParameterNotFound:
            return None

    def _fetch_gcp_secret(self) -> Optional[str]:
        credentials, project_id = GCP.get_credentials()
        sm_client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        name = f"projects/{project_id}/secrets/opta-{self.layer.get_env()}-runx-api-key/versions/1"
        try:
            # Access the secret version.
            response = sm_client.access_secret_version(
                request=secretmanager.AccessSecretVersionRequest({"name": name})
            )
            return response.payload.data.decode("UTF-8")
        except NotFound:
            return None

    def set_secret(self) -> None:
        while True:
            value = click.prompt("Please enter your runx api key", type=click.STRING,)
            try:
                self.fetch_jwt(value)
            except UserErrors:
                logger.warn(
                    "The api key which you passed was invalid, please provide a valid api key from runx"
                )
            else:
                break
        if self.layer.cloud == "aws":
            return self._set_aws_secret(value)
        elif self.layer.cloud == "google":
            return self._set_gcp_secret(value)
        else:
            raise Exception("Can not handle secrets of type")

    def _set_aws_secret(self, secret: str) -> None:
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        ssm_client: SSMClient = boto3.client("ssm", config=Config(region_name=region))
        ssm_client.put_parameter(
            Name=f"/opta-{self.layer.get_env()}/runx-api-key",
            Value=secret,
            Type="SecureString",
        )

    def _set_gcp_secret(self, secret: str) -> None:
        credentials, project_id = GCP.get_credentials()
        sm_client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        sm_secret = sm_client.create_secret(
            request=secretmanager.CreateSecretRequest(
                {
                    "parent": f"projects/{project_id}",
                    "secret_id": f"opta-{self.layer.get_env()}-runx-api-key",
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        )
        sm_client.add_secret_version(
            request=secretmanager.AddSecretVersionRequest(
                {"parent": sm_secret.name, "payload": {"data": secret.encode("utf-8")}}
            )
        )

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        api_key = self.fetch_secret()
        if api_key is None:
            raise Exception(
                "The api key seems to have just disappeared from the secret storage"
            )
        validation_data, jwt = self.fetch_jwt(api_key)
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
                "argv": sys.argv[:],
            },
            "time": datetime.utcnow().isoformat(),
        }
        if not is_environment:
            body["environment_name"] = self.layer.parent.name  # type: ignore
        logger.debug("Sending layer deployment data over to opta backend")
        resp = requests.post(
            f"https://{OPTA_DOMAIN}{url_path}", json=body, headers={"opta": jwt}
        )
        if resp.status_code != 201:
            raise Exception(
                f"Invalid response when attempting to send data to backend: {resp.json()}"
            )

    def fetch_jwt(self, api_key: str) -> Tuple[dict, str]:
        resp = requests.post(
            f"https://{OPTA_DOMAIN}/user/apikeys/validate", json={"api_key": api_key}
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
