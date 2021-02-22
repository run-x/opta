# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from opta.layer import Layer
from opta.module_processors.k8s_service import K8sServiceProcessor


class TestK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 5)
        mocked_process = mocker.patch(
            "opta.module_processors.k8s_service.K8sModuleProcessor.process"
        )
        K8sServiceProcessor(app_module, layer).process(5)
        mocked_process.assert_called_once_with(5)
        assert app_module.data["secrets"] == [
            {"name": "BALONEY", "value": ""},
            {"name": "database_db_user", "value": "${{module.database.db_user}}"},
            {"name": "database_db_name", "value": "${{module.database.db_name}}"},
            {"name": "database_db_password", "value": "${{module.database.db_password}}"},
            {"name": "database_db_host", "value": "${{module.database.db_host}}"},
            {"name": "redis_cache_host", "value": "${{module.redis.cache_host}}"},
            {
                "name": "redis_cache_auth_token",
                "value": "${{module.redis.cache_auth_token}}",
            },
            {"name": "docdb_db_user", "value": "${{module.docdb.db_user}}"},
            {"name": "docdb_db_host", "value": "${{module.docdb.db_host}}"},
            {"name": "docdb_db_password", "value": "${{module.docdb.db_password}}"},
        ]
        assert app_module.data["iam_policy"] == {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DescribeCluster",
                    "Action": ["eks:DescribeCluster"],
                    "Effect": "Allow",
                    "Resource": ["*"],
                },
                {
                    "Sid": "ReadBuckets",
                    "Action": ["s3:GetObject*", "s3:ListBucket"],
                    "Effect": "Allow",
                    "Resource": ["arn:aws:s3:::bucket1", "arn:aws:s3:::bucket1/*"],
                },
                {
                    "Sid": "WriteBuckets",
                    "Action": [
                        "s3:GetObject*",
                        "s3:PutObject*",
                        "s3:DeleteObject*",
                        "s3:ListBucket",
                    ],
                    "Effect": "Allow",
                    "Resource": ["arn:aws:s3:::bucket2", "arn:aws:s3:::bucket2/*"],
                },
            ],
        }

    def test_bad_rds_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 5)
        app_module.data["links"] = []
        app_module.data["links"].append({"database": "read"})
        with pytest.raises(Exception):
            K8sServiceProcessor(app_module, layer).process(5)

    def test_bad_redis_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 5)
        app_module.data["links"] = []
        app_module.data["links"].append({"redis": "read"})
        with pytest.raises(Exception):
            K8sServiceProcessor(app_module, layer).process(5)

    def test_bad_docdb_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 5)
        app_module.data["links"] = []
        app_module.data["links"].append({"docdb": "read"})
        with pytest.raises(Exception):
            K8sServiceProcessor(app_module, layer).process(5)

    def test_bad_s3_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "module_processors",
                "dummy_config1.yaml",
            ),
            None,
        )
        app_module = layer.get_module("app", 5)
        app_module.data["links"] = []
        app_module.data["links"].append({"bucket1": "blah"})
        with pytest.raises(Exception):
            K8sServiceProcessor(app_module, layer).process(5)
