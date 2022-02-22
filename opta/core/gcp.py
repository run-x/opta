import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import google.auth.transport.requests
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from googleapiclient import discovery

from opta.core.cloud_client import CloudClient
from opta.exceptions import UserErrors
from opta.utils import fmt_msg, json, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class GCP(CloudClient):
    project_id: Optional[str] = None
    credentials: Optional[Credentials] = None

    def __init__(self, layer: "Layer"):
        self.layer = layer
        self.region = layer.root().providers["google"]["region"]
        super().__init__(layer)

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

        # For some non-service account credentials, an access token is generated with
        # an expiry time, which must be occasionally refreshed.
        if not cls.using_service_account():
            cls.credentials.refresh(google.auth.transport.requests.Request())

        return cls.credentials, cls.project_id  # type: ignore

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

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        try:
            blob = storage.Blob(config_path, bucket_object)
            return json.loads(blob.download_as_text())
        except Exception:  # Backwards compatibility
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    def list_child_config_names(self) -> List[str]:
        bucket_name = self.layer.state_storage()
        gcs_config_dir = "opta_config/"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        try:
            bucket_object = gcs_client.get_bucket(bucket_name)
        except NotFound:
            logger.warn(
                "Couldn't find the state bucket, must have already been destroyed in a previous destroy run"
            )
            return []
        blobs: List[storage.Blob] = list(
            gcs_client.list_blobs(bucket_object, prefix=gcs_config_dir)
        )
        configs = [blob.name[len(gcs_config_dir) :] for blob in blobs]
        if self.layer.name in configs:
            configs.remove(self.layer.name)
        return configs

    def get_configuration_details(self, config_name: str) -> Dict[str, Any]:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{config_name}"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        blob = storage.Blob(config_path, bucket_object)
        config_details = json.loads(blob.download_as_text())
        return config_details["original_spec"]

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        blob = storage.Blob(config_path, bucket_object)
        blob.upload_from_string(json.dumps(self.layer.structured_config()))
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

    def delete_remote_state(self) -> None:
        bucket = self.layer.state_storage()
        tfstate_path = f"{self.layer.name}/default.tfstate"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        try:
            bucket_object.delete_blob(tfstate_path)
        except NotFound:
            logger.warn(f"Did not find opta tf state {tfstate_path} to delete")
        logger.info(f"Deleted opta tf state for {self.layer.name}")

    def get_current_zones(self, max_number: int = 3) -> List[str]:
        credentials, project_id = self.get_credentials()
        service = discovery.build(
            "compute", "v1", credentials=credentials, static_discovery=False
        )
        request = service.zones().list(
            project=project_id,
            filter=f'(region = "https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{GCP(self.layer).region}")',
        )
        response: Dict = request.execute()
        return sorted([x["name"] for x in response.get("items", [])])[:max_number]

    def get_terraform_lock_id(self) -> str:
        bucket = self.layer.state_storage()
        tf_lock_path = f"{self.layer.name}/default.tflock"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        try:
            tf_lock_blob = bucket_object.get_blob(tf_lock_path)
            return str(tf_lock_blob.generation)
        except Exception:  # Backwards compatibility
            logger.debug("No Terraform Lock state exists.")
            return ""

    def force_delete_terraform_lock_id(self) -> None:
        logger.info(
            "Trying to Remove the lock forcefully. Will try deleting TF Lock File."
        )
        bucket = self.layer.state_storage()
        tf_lock_path = f"{self.layer.name}/default.tflock"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        bucket_object.delete_blob(tf_lock_path)

    @classmethod
    def get_config_map(cls) -> Dict[str, List[str]]:
        prefix = "opta_config/"
        credentials, project_id = cls.get_credentials()
        storage_client = storage.Client(project=project_id, credentials=credentials)
        opta_config_map = {}
        for bucket in storage_client.list_buckets():
            config_list = []
            for response in storage_client.list_blobs(
                bucket.name, prefix=prefix, delimiter="/"
            ):
                config_list.append(response.name[len(prefix) :])
            if config_list:
                opta_config_map[bucket.name] = config_list
        return opta_config_map

    @classmethod
    def get_detailed_config_map(
        cls, environment: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        prefix = "opta_config/"
        credentials, project_id = cls.get_credentials()
        storage_client = storage.Client(project=project_id, credentials=credentials)
        opta_config_detailed_map = {}
        for bucket in storage_client.list_buckets():
            detailed_config = {}
            for response in storage_client.list_blobs(
                bucket.name, prefix=prefix, delimiter="/"
            ):
                blob = storage.Blob(response.name, bucket)
                detailed_config[response.name[len(prefix) :]] = json.loads(
                    blob.download_as_text()
                )["original_spec"]
            if detailed_config:
                opta_config_detailed_map[bucket.name] = detailed_config
        return opta_config_detailed_map
