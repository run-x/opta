from typing import Any, Dict

from pytest_mock import MockFixture

from opta.core.aws import AWS
from tests.utils import mocked_function

HOSTED_ZONE_RECORDS = {
    "ResourceRecordSets": [
        {"Name": "foo", "Type": "SOA", "Region": "us-east-1"},
        {"Name": "bar", "Type": "NS", "Region": "us-east-1"},
        {"Name": "baz", "Type": "CNAME", "Region": "us-east-1"},
    ]
}


class TestAWS:
    def test_delete_hosted_zone(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.aws.AWS._wait_for_route53_delete_completion")
        mocked_aws_client = mocker.patch("opta.core.aws.boto3.client").return_value
        mocked_aws_client.list_resource_record_sets = mocked_function(
            return_value=HOSTED_ZONE_RECORDS
        )

        change_resource_record_sets_call_args: Dict[str, Any] = {}
        mocked_aws_client.change_resource_record_sets = mocked_function(
            call_args_placeholder=change_resource_record_sets_call_args
        )
        AWS.delete_hosted_zone("fake_zone_id")

        # Only the CNAME (non-required) record should be deleted, not the SOA or NS records.
        assert change_resource_record_sets_call_args["kwargs"]["ChangeBatch"][
            "Changes"
        ] == [
            {
                "Action": "DELETE",
                "ResourceRecordSet": {
                    "Name": "baz",
                    "Region": "us-east-1",
                    "Type": "CNAME",
                },
            }
        ]
