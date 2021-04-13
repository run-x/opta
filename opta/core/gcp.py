from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import google.auth.transport.requests
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError, RefreshError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from googleapiclient import discovery

from opta.exceptions import UserErrors
from opta.utils import fmt_msg, logger

if TYPE_CHECKING:
    from opta.layer import Layer


class GCP:
    project_id: Optional[str] = None
    credentials: Optional[Credentials] = None

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
        try:
            # Refresh credentials to get new access token
            cls.credentials.refresh(google.auth.transport.requests.Request())
        except RefreshError:
            logger.info(
                fmt_msg(
                    """
                Tried refreshing credentials and failed. Assuming this user/service account
                doesn't have the permissions to do so. Continuing anyways.
                """
                )
            )
        return cls.credentials, cls.project_id  # type: ignore

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
