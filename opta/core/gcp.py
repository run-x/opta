import os
import time
from os import remove
from os.path import exists, getmtime
from shutil import which
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import google.auth.transport.requests
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import storage  # type: ignore
from google.cloud.container_v1 import ClusterManagerClient
from google.cloud.exceptions import NotFound
from google.cloud.storage import Bucket
from google.oauth2 import service_account
from googleapiclient import discovery

import opta.constants as constants
from opta.constants import ONE_WEEK_UNIX
from opta.core.cloud_client import CloudClient
from opta.exceptions import MissingState, UserErrors
from opta.utils import fmt_msg, json, logger, yaml
from opta.utils.dependencies import ensure_installed

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class GCP(CloudClient):
    project_id: Optional[str] = None
    credentials: Optional[Credentials] = None

    def __init__(self, layer: Optional["Layer"] = None):
        if layer:
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
        return self._download_remote_blob(bucket_object, config_path)

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
            logger.warning(f"Did not find opta config {config_path} to delete")
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
            logger.warning(f"Did not find opta tf state {tfstate_path} to delete")
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

    def bucket_exists(self, bucket_name: str) -> bool:
        credentials, project_id = GCP.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        try:
            _ = gcs_client.get_bucket(bucket_name)
        except NotFound:
            return False
        return True

    def get_all_remote_configs(self) -> Dict[str, Dict[str, "StructuredConfig"]]:
        prefix = "opta_config/"
        credentials, project_id = self.get_credentials()
        storage_client = storage.Client(project=project_id, credentials=credentials)
        opta_configs = {}
        for bucket in storage_client.list_buckets(prefix="opta-tf-state"):
            config = {}
            for response in storage_client.list_blobs(
                bucket.name, prefix=prefix, delimiter="/"
            ):
                structured_config = self._download_remote_blob(bucket, response.name)
                if structured_config:
                    config[response.name[len(prefix) :]] = structured_config
            if config:
                opta_configs[bucket.name] = config
        return opta_configs

    @staticmethod
    def _download_remote_blob(bucket: Bucket, key: str) -> Optional["StructuredConfig"]:
        try:
            blob = storage.Blob(key, bucket)
            return json.loads(blob.download_as_text())
        except Exception:  # Backwards compatibility
            logger.debug(
                "Could not successfully download and parse any pre-existing config"
            )
            return None

    def cluster_exist(self) -> bool:
        credentials = self.get_credentials()[0]
        region, project_id = self.get_cluster_env()
        cluster_name = self.layer.get_cluster_name()
        gke_client = ClusterManagerClient(credentials=credentials)
        try:
            gke_client.get_cluster(
                name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
            )
            return True
        except NotFound:
            return False

    def get_cluster_env(self) -> Tuple[str, str]:
        googl_provider = self.layer.root().providers["google"]
        return googl_provider["region"], googl_provider["project"]

    def get_kube_context_name(self) -> str:
        region, project_id = self.get_cluster_env()
        # Get the environment's account details from the opta config
        cluster_name = self.layer.get_cluster_name()
        return f"{project_id}_{region}_{cluster_name}"

    def set_kube_config(self) -> None:
        ensure_installed("gcloud")
        kube_config_file_name = self.layer.get_kube_config_file_name()
        if exists(kube_config_file_name):
            if getmtime(kube_config_file_name) > time.time() - ONE_WEEK_UNIX:
                constants.GENERATED_KUBE_CONFIG = kube_config_file_name
                return
            else:
                remove(kube_config_file_name)

        credentials = self.get_credentials()[0]
        region, project_id = self.get_cluster_env()
        cluster_name = self.layer.get_cluster_name()

        if not self.cluster_exist():
            raise Exception(
                "The GKE cluster name could not be determined -- please make sure it has been applied in the environment."
            )

        gke_client = ClusterManagerClient(credentials=credentials)
        cluster_data = gke_client.get_cluster(
            name=f"projects/{project_id}/locations/{region}/clusters/{cluster_name}"
        )

        cluster_ca_certificate = cluster_data.master_auth.cluster_ca_certificate
        cluster_endpoint = f"https://{cluster_data.endpoint}"
        gcloud_path = which("gcloud")
        kube_context_name = self.get_kube_context_name()

        cluster_config = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "cluster": {
                        "server": cluster_endpoint,
                        "certificate-authority-data": cluster_ca_certificate,
                    },
                    "name": kube_context_name,
                }
            ],
            "contexts": [
                {
                    "context": {"cluster": kube_context_name, "user": kube_context_name},
                    "name": kube_context_name,
                }
            ],
            "current-context": kube_context_name,
            "preferences": {},
            "users": [
                {
                    "name": kube_context_name,
                    "user": {
                        "auth-provider": {
                            "name": "gcp",
                            "config": {
                                "cmd-args": "config config-helper --format=json",
                                "cmd-path": gcloud_path,
                                "expiry-key": "{.credential.token_expiry}",
                                "token-key": "{.credential.access_token}",
                            },
                        }
                    },
                }
            ],
        }
        with open(kube_config_file_name, "w") as f:
            yaml.dump(cluster_config, f)
        constants.GENERATED_KUBE_CONFIG = kube_config_file_name
        return

    def get_remote_state(self) -> str:
        bucket = self.layer.state_storage()
        tfstate_path = f"{self.layer.name}/default.tfstate"
        credentials, project_id = self.get_credentials()
        gcs_client = storage.Client(project=project_id, credentials=credentials)
        bucket_object = gcs_client.get_bucket(bucket)
        tf_state = self._download_remote_blob(bucket_object, tfstate_path)
        if tf_state is None:
            raise MissingState("TF state does not exist.")
        return json.dumps(tf_state, indent=4)
