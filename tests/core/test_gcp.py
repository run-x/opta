from unittest.mock import Mock

import pytest
from google.auth.credentials import Credentials
from google.cloud.storage import Blob, Bucket, Client
from pytest import fixture
from pytest_mock import MockFixture

from opta.core.gcp import GCP
from opta.exceptions import MissingState
from opta.layer import Layer


class TestGcp:
    @fixture
    def gcp_layer(self) -> Mock:
        layer = Mock(spec=Layer)
        layer.parent = None
        layer.cloud = "aws"
        layer.name = "mock_name"
        layer.org_name = "mock_org_name"
        layer.providers = {"google": {"region": "us-central1", "project": "mock_project"}}

        layer.root.return_value = layer
        layer.gen_providers.return_value = {
            "terraform": {
                "backend": {
                    "gcs": {
                        "bucket": f"opta-tf-state-{layer.org_name}-{layer.name}",
                        "prefix": "mock",
                    }
                }
            },
            "provider": {"google": {"region": "us-central1", "project": "mock_project"}},
        }

        return layer

    def test_get_terraform_lock_id(self, mocker: MockFixture, gcp_layer: Layer) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )

        mock_gcs_client_instance = mocker.Mock(spec=Client)
        mock_gcs_bucket_instance = mocker.Mock(spec=Bucket)
        mock_gcs_tf_lock_blob = mocker.Mock(spec=Blob)
        mocker.patch(
            "opta.core.gcp.storage.Client", return_value=mock_gcs_client_instance
        )
        mock_gcs_client_instance.get_bucket.return_value = mock_gcs_bucket_instance
        mock_gcs_bucket_instance.get_blob.return_value = mock_gcs_tf_lock_blob
        mock_gcs_tf_lock_blob.generation = 1234567890

        assert GCP(gcp_layer).get_terraform_lock_id() == "1234567890"

    def test_force_delete_terraform_lock_id(
        self, mocker: MockFixture, gcp_layer: Layer
    ) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )

        mock_gcs_client_instance = mocker.Mock(spec=Client)
        mock_gcs_bucket_instance = mocker.Mock(spec=Bucket)
        mocker.patch(
            "opta.core.gcp.storage.Client", return_value=mock_gcs_client_instance
        )
        mock_gcs_client_instance.get_bucket.return_value = mock_gcs_bucket_instance
        GCP(gcp_layer).force_delete_terraform_lock_id()

        mock_gcs_bucket_instance.delete_blob.assert_called_once_with(
            f"{gcp_layer.name}/default.tflock"
        )

    def test_get_all_remote_configs_configuration_present(
        self, mocker: MockFixture
    ) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )
        mock_storage_instance = mocker.Mock(spec=Client)
        mock_bucket_instance = mocker.Mock(spec=Bucket)
        mock_bucket_instance.name = "test"
        mock_blob_list_blob_instance = mocker.Mock(spec=Blob)
        mock_blob_list_blob_instance.name = "opta_config/test-config"
        mock_storage_instance.list_buckets.return_value = [mock_bucket_instance]
        mock_storage_instance.list_blobs.return_value = [mock_blob_list_blob_instance]
        mock_download_remote_blob = mocker.patch(
            "opta.core.gcp.GCP._download_remote_blob",
            return_value={
                "opta_version": "dev",
                "date": "test_datetime",
                "original_spec": "actual_config",
                "defaults": {},
            },
        )

        mocker_list_bucket_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_buckets",
            return_value=[mock_bucket_instance],
        )
        mocker_list_blob_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_blobs",
            return_value=[mock_blob_list_blob_instance],
        )

        detailed_config_map = GCP().get_all_remote_configs()

        mocker_list_bucket_call.assert_called_once()
        mocker_list_blob_call.assert_called_once_with(
            mock_bucket_instance.name, prefix="opta_config/", delimiter="/"
        )
        mock_download_remote_blob.assert_called_once_with(
            mock_bucket_instance, mock_blob_list_blob_instance.name
        )
        assert detailed_config_map == {
            "test": {
                "test-config": {
                    "opta_version": "dev",
                    "date": "test_datetime",
                    "original_spec": "actual_config",
                    "defaults": {},
                }
            }
        }

    def test_get_all_remote_configs_configuration_not_present(
        self, mocker: MockFixture
    ) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )
        mock_storage_instance = mocker.Mock(spec=Client)
        mock_bucket_instance = mocker.Mock(spec=Bucket)
        mock_bucket_instance.name = "test"
        mock_storage_instance.list_buckets.return_value = [mock_bucket_instance]
        mock_storage_instance.list_blobs.return_value = []

        mocker_list_bucket_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_buckets",
            return_value=[mock_bucket_instance],
        )
        mocker_list_blob_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_blobs", return_value=[]
        )
        mock_download_remote_blob = mocker.patch(
            "opta.core.gcp.GCP._download_remote_blob"
        )

        detailed_config_map = GCP().get_all_remote_configs()

        assert detailed_config_map == {}
        mocker_list_bucket_call.assert_called_once()
        mocker_list_blob_call.assert_called_once_with(
            mock_bucket_instance.name, prefix="opta_config/", delimiter="/"
        )
        mock_download_remote_blob.assert_not_called()

    def test_get_all_remote_configs_bucket_not_present(self, mocker: MockFixture) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )
        mock_storage_instance = mocker.Mock(spec=Client)
        mock_bucket_instance = mocker.Mock(spec=Bucket)
        mock_bucket_instance.name = "test"
        mock_storage_instance.list_buckets.return_value = []
        mock_storage_instance.list_blobs.return_value = []

        mocker_list_bucket_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_buckets", return_value=[]
        )
        mocker_list_blob_call = mocker.patch(
            "opta.core.gcp.storage.Client.list_blobs", return_value=[]
        )
        mock_download_remote_blob = mocker.patch(
            "opta.core.gcp.GCP._download_remote_blob"
        )

        detailed_config_map = GCP().get_all_remote_configs()

        assert detailed_config_map == {}
        mocker_list_bucket_call.assert_called_once()
        mocker_list_blob_call.assert_not_called()
        mock_download_remote_blob.assert_not_called()

    def test_get_remote_state(self, mocker: MockFixture, gcp_layer: Mock) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )
        mock_bucket_instance = mocker.Mock(spec=Bucket)
        mocker.patch(
            "opta.core.gcp.storage.Client.get_bucket", return_value=mock_bucket_instance
        )
        mock_download_remote_blob = mocker.patch(
            "opta.core.gcp.GCP._download_remote_blob", return_value="""{"test": "test}"""
        )
        GCP(layer=gcp_layer).get_remote_state()
        mock_download_remote_blob.assert_called_once_with(
            mock_bucket_instance, f"{gcp_layer.name}/default.tfstate"
        )

    def test_get_remote_state_state_does_not_exist(
        self, mocker: MockFixture, gcp_layer: Mock
    ) -> None:
        mocker.patch(
            "opta.core.gcp.default",
            return_value=(mocker.Mock(spec=Credentials), "dummy_project_id"),
        )
        mock_bucket_instance = mocker.Mock(spec=Bucket)
        mocker.patch(
            "opta.core.gcp.storage.Client.get_bucket", return_value=mock_bucket_instance
        )
        mock_download_remote_blob = mocker.patch(
            "opta.core.gcp.GCP._download_remote_blob", return_value=None
        )
        with pytest.raises(MissingState):
            GCP(layer=gcp_layer).get_remote_state()
        mock_download_remote_blob.assert_called_once_with(
            mock_bucket_instance, f"{gcp_layer.name}/default.tfstate"
        )
