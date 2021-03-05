import boto3
import json

from botocore.config import Config
from opta.layer import Layer
from opta.utils import deep_merge

class AWS:
    def __init__(self, layer: Layer):
        providers = layer.gen_providers(0)
        self.region = providers["aws"]["region"]
        self.account_id = providers["aws"]["allowed_account_ids"]

    # Fetches AWS resources tagged with "opta: true"
    # Works on most resources, but not all (ex. IAM, elasticache subnet groups)
    # Unfortunately this is the best single API to get AWS resources, since there's
    # no API that can fetch all resources.
    #
    # The returned structure is
    # {
    #    "terraform.address" : "aws resource arn"
    # }
    def get_opta_resources(self):
        regional_resources = self._get_opta_resources(self.region)
        global_resources = self._get_opta_resources()
        return deep_merge(regional_resources, global_resources)

    def _get_opta_resources(self, region = None) -> dict:
        extra_args = {} if region is None else {"config": Config(region_name=region)}
        client = boto3.client("resourcegroupstagingapi", **extra_args)

        state = client.get_resources(TagFilters=[{"Key": "opta", "Values": ["true"]}])
        resources = state["ResourceTagMappingList"]
        
        resources_map = {}
        for resource in resources:
            arn = resource["ResourceARN"]
            for tag in resource["Tags"]:
                if tag["Key"] == "tf_address":
                    terraform_address = tag["Value"]
                    resources_map[terraform_address] = arn
    
        return resources_map
