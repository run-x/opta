# type: ignore
import os

import pytest
from pytest_mock import MockFixture

from modules.aws_k8s_service.aws_k8s_service import AwsK8sServiceProcessor
from opta.layer import Layer


class TestK8sServiceProcessor:
    def test_all_good(self, mocker: MockFixture):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        mocked_process = mocker.patch(
            "modules.aws_k8s_service.aws_k8s_service.AWSK8sModuleProcessor.process"
        )
        AwsK8sServiceProcessor(app_module, layer).process(idx)
        mocked_process.assert_called_once_with(idx)
        assert app_module.data["env_vars"] == [{"name": "A", "value": "B"}]
        assert app_module.data["link_secrets"] == [
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
            {"name": "DBUSER2", "value": "${{module.database2.db_user}}"},
            {"name": "DBNAME2", "value": "${{module.database2.db_name}}"},
            {"name": "BLAH", "value": "${{module.database2.db_password}}"},
            {"name": "DBHOST2", "value": "${{module.database2.db_host}}"},
            {"name": "CACHEHOST2", "value": "${{module.redis2.cache_host}}"},
            {"name": "CACHEAUTH2", "value": "${{module.redis2.cache_auth_token}}"},
            {"name": "DOCDBUSER2", "value": "${{module.docdb2.db_user}}"},
            {"name": "DOCDBHOST2", "value": "${{module.docdb2.db_host}}"},
            {"name": "DOCDBPASSWORD2", "value": "${{module.docdb2.db_password}}"},
        ]
        # this field has been deprecated, no longer populated
        assert "manual_secrets" not in app_module.data.keys()
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
                    "Resource": [
                        "arn:aws:s3:::bucket2",
                        "arn:aws:s3:::bucket3",
                        "arn:aws:s3:::bucket2/*",
                        "arn:aws:s3:::bucket3/*",
                    ],
                },
                {
                    "Action": [
                        "sqs:SendMessage",
                        "sqs:SendMessageBatch",
                        "sqs:GetQueueUrl",
                        "sqs:GetQueueAttributes",
                        "sqs:DeleteMessageBatch",
                        "sqs:DeleteMessage",
                    ],
                    "Effect": "Allow",
                    "Resource": ["${{module.queue.queue_arn}}"],
                    "Sid": "PublishQueues",
                },
                {
                    "Action": [
                        "sqs:ReceiveMessage",
                        "sqs:GetQueueUrl",
                        "sqs:GetQueueAttributes",
                    ],
                    "Effect": "Allow",
                    "Resource": ["${{module.queue.queue_arn}}"],
                    "Sid": "SubscribeQueues",
                },
                {
                    "Action": ["sns:Publish"],
                    "Effect": "Allow",
                    "Resource": ["${{module.topic.topic_arn}}"],
                    "Sid": "PublishSns",
                },
                {
                    "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
                    "Effect": "Allow",
                    "Resource": [
                        "${{module.queue.kms_arn}}",
                        "${{module.topic.kms_arn}}",
                        "${{module.dynamo.kms_arn}}",
                    ],
                    "Sid": "KMSWrite",
                },
                {
                    "Action": ["kms:Decrypt"],
                    "Effect": "Allow",
                    "Resource": ["${{module.queue.kms_arn}}"],
                    "Sid": "KMSRead",
                },
                {
                    "Action": [
                        "dynamodb:BatchWriteItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:PartiQLDelete",
                        "dynamodb:PartiQLInsert",
                        "dynamodb:PartiQLUpdate",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:ListTables",
                        "dynamodb:BatchGetItem",
                        "dynamodb:Describe*",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:PartiQLSelect",
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        "${{module.dynamo.table_arn}}",
                        "${{module.dynamo.table_arn}}/index/*",
                    ],
                    "Sid": "DynamodbWrite",
                },
            ],
        }

    def test_get_event_properties(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        assert AwsK8sServiceProcessor(app_module, layer).get_event_properties() == {
            "module_aws_k8s_service": 2
        }

    def test_bad_rds_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        app_module.data["links"] = []
        app_module.data["links"].append({"database": "read"})
        with pytest.raises(Exception):
            AwsK8sServiceProcessor(app_module, layer).process(5)

    def test_bad_redis_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        app_module.data["links"] = []
        app_module.data["links"].append({"redis": "read"})
        with pytest.raises(Exception):
            AwsK8sServiceProcessor(app_module, layer).process(5)

    def test_bad_docdb_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        app_module.data["links"] = []
        app_module.data["links"].append({"docdb": "read"})
        with pytest.raises(Exception):
            AwsK8sServiceProcessor(app_module, layer).process(idx)

    def test_bad_s3_permission(self):
        layer = Layer.load_from_yaml(
            os.path.join(
                os.getcwd(), "tests", "fixtures", "dummy_data", "dummy_config1.yaml"
            ),
            None,
        )
        idx = len(layer.modules)
        app_module = layer.get_module("app", idx)
        app_module.data["links"] = []
        app_module.data["links"].append({"bucket1": "blah"})
        with pytest.raises(Exception):
            AwsK8sServiceProcessor(app_module, layer).process(idx)
