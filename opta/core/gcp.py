import os
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import google.auth.transport.requests
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from googleapiclient import discovery

from opta.exceptions import UserErrors
from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer


class GCP:
    project_id: Optional[str] = None
    credentials: Optional[Credentials] = None
    last_refreshed = datetime(1, 1, 1, 0, 0, 0)

    def __init__(self, layer: "Layer"):
        self.layer = layer
        providers = layer.root().gen_providers(0)["provider"]
        self.region = providers["google"]["region"]

    @classmethod
    def get_credentials(cls) -> Tuple[Credentials, str]:
        if cls.project_id is None or cls.credentials is None:
            try:
                cls.credentials, cls.project_id = default()
            except DefaultCredentialsError:
                raise UserErrors(
                    "Couldn't find default google credentials to use, pls run "
                    "`https://googleapis.dev/python/google-api-core/latest/auth.html#overview`"
                )
            except GoogleAuthError as e:
                raise UserErrors(*e.args)

        cls._refresh_token_if_necessary()
        return cls.credentials, cls.project_id  # type: ignore

    # For some credentials, an access token is generated with an expiration time.
    # Refresh the access token if it's expired.
    @classmethod
    def _refresh_token_if_necessary(cls) -> None:
        if cls.using_service_account():
            # Service account credentials don't have a refreshable token, so skip.
            return

        current_time = datetime.now()
        seconds_since_last_refresh = (current_time - cls.last_refreshed).total_seconds()
        if cls.credentials.expired or seconds_since_last_refresh > 30:  # type: ignore
            cls.credentials.refresh(google.auth.transport.requests.Request())  # type: ignore
            cls.last_refreshed = current_time

    @classmethod
    def using_service_account(cls) -> bool:
        credentials = cls.credentials or cls.get_credentials()[0]
        return type(credentials) == service_account.Credentials

    @classmethod
    def get_service_account_key_path(cls) -> str:
        if not cls.using_service_account:
            raise Exception(
                "Tried getting service account key, but service account is not used."
            )

        service_account_key_file_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account_key_file_path is None:
            raise UserErrors(
                fmt_msg(
                    """
                If you're using a service account to authenticate with GCP, please make
                ~sure you set $GOOGLE_APPLICATION_CREDENTIALS to the absolute path of the
                ~service account json key file.
                """
                )
            )
        return service_account_key_file_path

    @classmethod
    def get_service_account_raw_credentials(cls) -> str:
        service_account_key_file_path = cls.get_service_account_key_path()
        with open(service_account_key_file_path, "r") as f:
            service_account_key = f.read()
        return service_account_key

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self, config_data: str) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        blob = storage.Blob(config_path, bucket_object)
        blob.upload_from_string(config_data)
        logger.debug("Uploaded opta config to gcs")

    def delete_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        try:
            bucket_object.delete_blob(config_path)
        except NotFound:
            logger.warn(f"Did not find opta config {config_path} to delete")
        logger.info("Deleted opta config from gcs")

    def get_current_zones(self, max_number: int = 3) -> List[str]:
        credentials, project_id = self.get_credentials()
        service = discovery.build("compute", "v1", credentials=credentials)
        request = service.zones().list(
            project=project_id,
            filter=f'(region = "https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{GCP(self.layer).region}")',
        )
        response: Dict = request.execute()
        return sorted([x["name"] for x in response.get("items", [])])[:max_number]
