from unittest.mock import Mock

from google.auth.credentials import Credentials
from google.cloud.storage import Blob, Bucket, Client
from pytest import fixture
from pytest_mock import MockFixture

from opta.core.gcp import GCP
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
