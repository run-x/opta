from typing import TYPE_CHECKING, Optional

import boto3
from botocore.config import Config

from opta.utils import deep_merge

if TYPE_CHECKING:
    from opta.layer import Layer


class AWS:
    def __init__(self, layer: "Layer"):
        self.layer_name = layer.name

        providers = layer.root().gen_providers(0)["provider"]
        self.region = providers["aws"]["region"]
        self.account_id = providers["aws"]["allowed_account_ids"][0]

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
        regional_resources = self._get_opta_resources(self.region)
        global_resources = self._get_opta_resources()
        return deep_merge(regional_resources, global_resources)

    def _get_opta_resources(self, region: Optional[str] = None) -> dict:
        extra_args = {} if region is None else {"config": Config(region_name=region)}
        client = boto3.client("resourcegroupstaggingapi", **extra_args)

        state = client.get_resources(
            TagFilters=[
                {"Key": "opta", "Values": ["true"]},
                {"Key": "layer", "Values": [self.layer_name]},
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

    # AWS Resource ARNs can be one of the following 3 formats:
    # 1). arn:partition:service:region:account-id:resource-id
    # 2). arn:partition:service:region:account-id:resource-type/resource-id
    # 3). arn:partition:service:region:account-id:resource-type:resource-id
    @staticmethod
    def get_resource_id(resource_arn: str) -> str:
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
