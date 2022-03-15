import io
from typing import Any, Generator, List

import pytest
from botocore.stub import Stubber
from pytest_mock import MockFixture

from opta.cloud.aws import _client
from opta.cloud.aws.state import S3Store
from opta.core.terraform2.state import StateNotFoundError, StoreConfig
from opta.core.terraform2.terraform_file import TerraformFile
from opta.exceptions import UserErrors


class TestS3Store:
    def test_configure_terraform_file(
        self, store: S3Store, bucket: str, region: str
    ) -> None:
        actual = TerraformFile()
        store.configure_terraform_file(actual)

        expected = TerraformFile()
        expected.backend_id = "s3"
        expected.backend = {
            "bucket": bucket,
            "key": "bar",
            "dynamodb_table": bucket,
            "region": region,
        }

        assert actual.__to_json__() == expected.__to_json__()

    def test_is_storage_configured_exists(
        self, store: S3Store, stub_s3: Stubber, bucket: str
    ) -> None:
        stub_s3.add_response(
            "get_bucket_encryption",
            {"ServerSideEncryptionConfiguration": {"Rules": []}},
            {"Bucket": bucket},
        )

        assert store.is_storage_configured() is True

    def test_is_storage_configured_missing(
        self, store: S3Store, stub_s3: Stubber
    ) -> None:
        stub_s3.add_client_error("get_bucket_encryption", "NoSuchBucket")

        assert store.is_storage_configured() is False

    def test_read_raw(self, store: S3Store, stub_s3: Stubber, bucket: str) -> None:
        expected = "foo"
        get_response = {"Body": io.StringIO(expected)}

        response = {"ContentLength": len(expected)}
        stub_s3.add_response("head_object", response, {"Bucket": bucket, "Key": "bar"})
        stub_s3.add_response(
            "get_object", {**response, **get_response}, {"Bucket": bucket, "Key": "bar"}
        )

        actual = store.read_raw()
        assert actual == expected

    def test_read_raw_missing(self, store: S3Store, stub_s3: Stubber) -> None:
        stub_s3.add_client_error("head_object", "404")

        with pytest.raises(StateNotFoundError):
            store.read_raw()

    def test_configure_bucket_exists(
        self, store: S3Store, stub_s3: Stubber, bucket: str
    ) -> None:
        stub_s3.add_response(
            "get_bucket_encryption",
            {"ServerSideEncryptionConfiguration": {"Rules": []}},
            {"Bucket": bucket},
        )
        store._configure_bucket()

    def test_configure_bucket_auth_failure(
        self, store: S3Store, stub_s3: Stubber
    ) -> None:
        stub_s3.add_client_error("get_bucket_encryption", "AuthFailure")

        with pytest.raises(UserErrors) as e:
            store._configure_bucket()

        assert "The AWS Credentials are not configured properly" in str(e.value)

    def test_configure_bucket_access_denied(
        self, store: S3Store, stub_s3: Stubber
    ) -> None:
        stub_s3.add_client_error("get_bucket_encryption", "AccessDenied")

        with pytest.raises(UserErrors) as e:
            store._configure_bucket()

        assert "We were unable to access the S3 bucket" in str(e.value)

    def test_configure_bucket_unknown_error(
        self, store: S3Store, stub_s3: Stubber
    ) -> None:
        stub_s3.add_client_error("get_bucket_encryption", "Foo", "bar")

        with pytest.raises(UserErrors) as e:
            store._configure_bucket()

        assert "Foo error with the message bar" in str(e.value)

    @pytest.mark.parametrize("waits", [0, 1])
    def test_configure_bucket(
        self, store: S3Store, region: str, bucket: str, waits: int, stub_s3: Stubber
    ) -> None:
        stub_s3.add_client_error("get_bucket_encryption", "NoSuchBucket")

        response = {
            "Location": "foo",
        }
        stub_s3.add_response(
            "create_bucket",
            response,
            {
                "Bucket": bucket,
                "CreateBucketConfiguration": {"LocationConstraint": region},
            },
        )

        head_request = {"Bucket": bucket}

        for _ in range(waits):
            stub_s3.add_client_error(
                "head_bucket",
                "NoSuchBucket",
                "404",
                http_status_code=404,
                expected_params=head_request,
            )

        stub_s3.add_response(
            "head_bucket", {"ResponseMetadata": {"HTTPStatusCode": 200}}, head_request
        )

        stub_s3.add_response(
            "put_bucket_encryption",
            {},
            {
                "Bucket": bucket,
                "ServerSideEncryptionConfiguration": {
                    "Rules": [
                        {
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "AES256"
                            }
                        },
                    ]
                },
            },
        )

        stub_s3.add_response(
            "put_bucket_versioning",
            {},
            {"Bucket": bucket, "VersioningConfiguration": {"Status": "Enabled"}},
        )
        stub_s3.add_response(
            "put_bucket_lifecycle",
            {},
            {
                "Bucket": bucket,
                "LifecycleConfiguration": {
                    "Rules": [
                        {
                            "ID": "default",
                            "Prefix": "/",
                            "Status": "Enabled",
                            "NoncurrentVersionTransition": {
                                "NoncurrentDays": 30,
                                "StorageClass": "GLACIER",
                            },
                            "NoncurrentVersionExpiration": {"NoncurrentDays": 60},
                            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 10},
                        },
                    ]
                },
            },
        )

        store._configure_bucket()

    def test_configure_dynamodb_table_exists(
        self, store: S3Store, stub_dynamodb: Stubber, bucket: str
    ) -> None:
        stub_dynamodb.add_response("describe_table", {}, {"TableName": bucket})
        store._configure_dynamodb_table()

    def test_configure_dynamodb_table_unknown_error(
        self, store: S3Store, stub_dynamodb: Stubber, bucket: str
    ) -> None:
        stub_dynamodb.add_client_error("describe_table", "Foo", "bar")

        with pytest.raises(UserErrors) as e:
            store._configure_dynamodb_table()

        assert "Foo error with the message bar" in str(e.value)

    def test_configure_dynamodb_table(
        self, store: S3Store, stub_dynamodb: Stubber, bucket: str
    ) -> None:
        stub_dynamodb.add_client_error("describe_table", "ResourceNotFoundException")

        stub_dynamodb.add_response(
            "create_table",
            {},
            {
                "TableName": bucket,
                "KeySchema": [{"AttributeName": "LockID", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "LockID", "AttributeType": "S"}
                ],
                "BillingMode": "PAY_PER_REQUEST",
            },
        )

        store._configure_dynamodb_table()

    def test_configure_iam(
        self, store: S3Store, stub_iam: Stubber, iam_service_linked_roles: List[str]
    ) -> None:
        for service in iam_service_linked_roles:
            stub_iam.add_response(
                "create_service_linked_role", {}, {"AWSServiceName": service}
            )

        store._configure_iam()

    def test_configure_iam_exists(
        self, store: S3Store, stub_iam: Stubber, iam_service_linked_roles: List[str]
    ) -> None:
        for service in iam_service_linked_roles:
            stub_iam.add_client_error(
                "create_service_linked_role",
                "InvalidInput",
                expected_params={"AWSServiceName": service},
            )

        store._configure_iam()

    @pytest.mark.parametrize("error_at", [0, 1])
    def test_configure_iam_error(
        self,
        store: S3Store,
        stub_iam: Stubber,
        iam_service_linked_roles: List[str],
        error_at: int,
    ) -> None:
        for idx, service in enumerate(iam_service_linked_roles):
            if idx == error_at:
                stub_iam.add_client_error(
                    "create_service_linked_role",
                    "Foo",
                    "Bar",
                    expected_params={"AWSServiceName": service},
                )
            elif idx < error_at:
                stub_iam.add_client_error(
                    "create_service_linked_role",
                    "InvalidInput",
                    expected_params={"AWSServiceName": service},
                )

        with pytest.raises(UserErrors) as e:
            store._configure_iam()

        assert "Foo error with the message Bar" in str(e.value)

    def test_validate_config(self, config: StoreConfig) -> None:
        config.region = None

        with pytest.raises(ValueError) as e:
            S3Store._validate_config(config)

        assert "region must be configured" in str(e.value)

    @pytest.fixture
    def iam_service_linked_roles(self) -> List[str]:
        return [
            "autoscaling.amazonaws.com",
            "elasticloadbalancing.amazonaws.com",
        ]

    @pytest.fixture(autouse=True)
    def stub_s3(self, region: str, mocker: MockFixture) -> Generator[Stubber, None, None]:
        yield from self.stub_service(mocker, "s3", region)

    @pytest.fixture(autouse=True)
    def stub_iam(self, mocker: MockFixture) -> Generator[Stubber, None, None]:
        yield from self.stub_service(mocker, "iam")

    @pytest.fixture(autouse=True)
    def stub_dynamodb(
        self, region: str, mocker: MockFixture
    ) -> Generator[Stubber, None, None]:
        yield from self.stub_service(mocker, "dynamodb", region)

    def stub_service(
        self, mocker: MockFixture, name: str, *args: Any
    ) -> Generator[Stubber, None, None]:
        client = getattr(_client, name)(*args)
        stubber = Stubber(client)
        mock = mocker.patch(f"opta.cloud.aws._client.{name}")
        mock.return_value = client

        with stubber:
            yield stubber

        stubber.assert_no_pending_responses()

    @pytest.fixture
    def bucket(self) -> str:
        return "opta-tf-state-foo-bar"

    @pytest.fixture
    def region(self) -> str:
        return "us-west-1"

    @pytest.fixture
    def config(self, region: str) -> StoreConfig:
        return StoreConfig("foo", "bar", region)

    @pytest.fixture
    def store(self, config: StoreConfig) -> S3Store:
        return S3Store(config)
