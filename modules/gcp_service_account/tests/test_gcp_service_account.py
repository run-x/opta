# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from modules.gcp_service_account.gcp_service_account import GcpServiceAccountProcessor
from opta.layer import Layer


class TestGCPK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "gcp_dummy_config.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        service_account_module = layer.get_module("blah", idx)
        GcpServiceAccountProcessor(service_account_module, layer).process(idx)
        assert service_account_module.data["read_buckets"] == [
            "${{module.bucket1.bucket_name}}"
        ]
        assert service_account_module.data["write_buckets"] == [
            "${{module.bucket2.bucket_name}}",
            "${{module.bucket3.bucket_name}}",
        ]

    def test_bad_gcs_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "gcp_dummy_config.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        app_module.data["links"] = []
        app_module.data["links"].append({"bucket1": "blah"})
        with pytest.raises(Exception):
            GcpServiceAccountProcessor(app_module, layer).process(idx)
