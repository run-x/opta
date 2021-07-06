from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable

REGIONS = [
    "us-east-2",
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "af-south-1",
    "ap-east-1",
    "ap-south-1",
    "ap-northeast-3",
    "ap-northeast-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-south-1",
    "eu-west-3",
    "eu-north-1",
    "me-south-1",
    "sa-east-1",
    "us-gov-east-1",
    "us-gov-west-1",
]


def validate(region_name: str) -> bool:
    return region_name in REGIONS


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "aws", "region"])
    set_path(d, v)
    return d


indented_regions = [f"\t{region}" for region in REGIONS]
region_string = "\n".join(indented_regions)

awsRegionVariable = TemplateVariable(
    prompt="AWS region (you can see a full list at https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)",
    applier=apply,
    validator=validate,
    error_message=f"Must be one of\n{region_string}",
    default_value="us-east-1",
)
