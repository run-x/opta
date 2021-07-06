from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable

REGIONS = [
    "asia-east1",
    "asia-east2",
    "asia-northeast1",
    "asia-northeast2",
    "asia-northeast3",
    "asia-south1",
    "asia-southeast1",
    "asia-southeast2",
    "australia-southeast1",
    "australia-southeast2",
    "europe-central2",
    "europe-north1",
    "europe-west1",
    "europe-west2",
    "europe-west3",
    "europe-west4",
    "europe-west6",
    "northamerica-northeast1",
    "southamerica-east1",
    "us-central1",
    "us-east1",
    "us-east4",
    "us-west1",
    "us-west2",
    "us-west3",
    "us-west4",
]


def validate(region_name: str) -> bool:
    return region_name in REGIONS


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "google", "region"])
    set_path(d, v)
    return d


indented_regions = [f"\t{region}" for region in REGIONS]
region_string = "\n".join(indented_regions)

gcpRegionVariable = TemplateVariable(
    prompt="GCP region (you can see a full list at https://cloud.google.com/compute/docs/regions-zones) ",
    applier=apply,
    validator=validate,
    error_message=f"Must be one of\n{region_string}",
    default_value="us-central1",
)
