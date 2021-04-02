from typing import TYPE_CHECKING, Optional, Tuple

import google.auth.transport.requests
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import storage
from google.cloud.exceptions import NotFound

from opta.exceptions import UserErrors
from opta.utils import logger

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
        # Refresh credentials to get new access token
        cls.credentials.refresh(google.auth.transport.requests.Request())
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
