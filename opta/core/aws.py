from time import sleep
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer


class AWS:
    def __init__(self, layer: "Layer"):
        self.layer = layer
        providers = layer.root().gen_providers(0)["provider"]
        self.region = providers["aws"]["region"]

    # Fetches AWS resources tagged with "opta: true"
    # Works on most resources, but not all (ex. IAM, elasticache subnet groups)
    # Unfortunately this is the best single API to get AWS resources, since there's
    # no API that can fetch all resources.
    #
    # The returned structure is
    # {
    #    "terraform.address" : "aws resource arn"
    # }
    def get_opta_resources(self) -> dict:
        client = boto3.client(
            "resourcegroupstaggingapi", config=Config(region_name=self.region)
        )

        state = client.get_resources(
            TagFilters=[
                {"Key": "opta", "Values": ["true"]},
                {"Key": "layer", "Values": [self.layer.name]},
            ]
        )
        resources = state["ResourceTagMappingList"]

        resources_map = {}
        for resource in resources:
            arn = resource["ResourceARN"]
            for tag in resource["Tags"]:
                if tag["Key"] == "tf_address":
                    terraform_address = tag["Value"]
                    resources_map[terraform_address] = arn

        return resources_map

    # Upload the current opta config to the state bucket, under opta_config/.
    def upload_opta_config(self, config: str) -> None:
        bucket = self.layer.state_storage()
        config_path = f"opta_config/{self.layer.name}"

        s3_client = boto3.client("s3")
        s3_client.upload_file(config, bucket, config_path)
        logger.debug("Uploaded opta config to s3")

    @staticmethod
    def delete_hosted_zone(zone_id: str) -> None:
        AWS._delete_hosted_zone_records(zone_id)

        client = boto3.client("route53")
        delete_state = client.delete_hosted_zone(Id=zone_id)
        delete_status = AWS._wait_for_route53_delete_completion(delete_state)

        print(f"Hosted zone ({zone_id}) deleted with status {delete_status}")

    @staticmethod
    # Before a hosted zone can be deleted, all of its non-required records must
    # be removed.
    def _delete_hosted_zone_records(zone_id: str) -> None:
        client = boto3.client("route53")
        # TODO: Pagination is necessary after 100+ records in a zone.
        list_resp = client.list_resource_record_sets(HostedZoneId=zone_id)
        records = list_resp["ResourceRecordSets"]

        non_required_records = [
            record for record in records if record["Type"] not in ["NS", "SOA"]
        ]
        if len(non_required_records) == 0:
            return

        delete_records_batch = list(
            map(
                lambda x: {"Action": "DELETE", "ResourceRecordSet": x},
                non_required_records,
            )
        )
        delete_state = client.change_resource_record_sets(
            HostedZoneId=zone_id, ChangeBatch={"Changes": delete_records_batch}
        )
        delete_status = AWS._wait_for_route53_delete_completion(delete_state)

        print(f"Records in hosted zone ({zone_id} deleted with status {delete_status}")

    @staticmethod
    def _wait_for_route53_delete_completion(delete_state: dict) -> str:
        client = boto3.client("route53")
        while delete_state["ChangeInfo"]["Status"] == "PENDING":
            sleep(5)
            logger.debug("AWS Route53 resource delete pending...")
            delete_state = client.get_change(Id=delete_state["ChangeInfo"]["Id"])

        return delete_state["ChangeInfo"]["Status"]


# AWS Resource ARNs can be one of the following 3 formats:
# 1). arn:partition:service:region:account-id:resource-id
# 2). arn:partition:service:region:account-id:resource-type/resource-id
# 3). arn:partition:service:region:account-id:resource-type:resource-id
def get_aws_resource_id(resource_arn: str) -> str:
    arn_parts = resource_arn.split(":")

    # Format 1:
    if len(arn_parts) == 6 and "/" not in arn_parts[-1]:
        return arn_parts[-1]

    # Format 2
    if len(arn_parts) == 6 and "/" in arn_parts[-1]:
        return arn_parts[-1].split("/")[1]

    # Format 3
    if len(arn_parts) == 7:
        return arn_parts[-1]

    raise Exception(f"Not a valid AWS arn: {resource_arn}")
