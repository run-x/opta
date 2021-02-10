import json
import os
import re
from typing import Any, List

import yaml

from opta.nice_subprocess import nice_run
from opta.utils import is_tool
from opta.var import TF_FILE_PATH

INSPECT_CONFIG = "inspect.yml"


def inspect_cmd() -> None:
    # Make sure the user has the prerequisite CLI tools installed
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")

    aws_region = _get_aws_region()

    # Fetch the inspect config template
    inspect_config_file_path = os.path.join(os.path.dirname(__file__), INSPECT_CONFIG)
    inspect_config = yaml.load(open(inspect_config_file_path), Loader=yaml.Loader)
    inspected_resource_mappings = inspect_config["resources"]

    # Fetch the terraform state
    resources = _fetch_terraform_resources()
    inspect_details = []
    for resource in resources:
        # Every terraform resource has an "address", and this is what
        # the inspect config matches on.
        resource_address = resource.get("address", "")

        # If the terraform resource address has "[0]" or "[#]" appending it, then
        # it's an instance of a cluster, in which case, skip.
        if re.match(r".*\[[0-9]+\]", resource_address):
            continue

        for inspect_key in inspected_resource_mappings:
            # For example, the inspect key may be "helm_release.k8s-service" and the full
            # resource address is "module.app.helm_release.k8s-service".
            if inspect_key in resource_address:
                resource_name = inspected_resource_mappings[inspect_key].get("name") or ""
                resource_description = inspected_resource_mappings[inspect_key].get("desc") or ""
                resource_template_url = inspected_resource_mappings[inspect_key].get("url") or ""

                resource_values = {"aws_region": aws_region}

                terraform_resource_values = resource.get("values")

                # Inspect key-specific logic
                print(inspect_key, terraform_resource_values.keys())
                if inspect_key == "helm_release.k8s-service" and "metadata" in terraform_resource_values:
                    k8s_metadata = terraform_resource_values["metadata"]
                    resource_values = {**resource_values, **_get_k8s_metadata_values(k8s_metadata)}
                    del terraform_resource_values["metadata"]

                for k, v in terraform_resource_values.items():
                    resource_values[k] = str(v)

                resource_url = resource_template_url.format(**resource_values)
                inspect_details.append(
                    (resource_name, resource_description, resource_url)
                )
                break

    inspect_details.sort()
    inspect_details.insert(0, ("NAME", "DESCRIPTION", "LINK"))
    column_print(inspect_details)


def _get_k8s_metadata_values(metadata: int):
    k8s_values = {}
    for chart in metadata:
        chart_values = json.loads(chart.get("values", "{}"))
        k8s_values = {**k8s_values, **chart_values}

    values = {}
    for k, v in k8s_values.items():
        values[f"k8s-{k}"] = v

    print(values.keys())
    return values


# Example resource fetched from terraform:
# {
#    "address":"module.app.aws_ecr_lifecycle_policy.repo_policy[0]",
#    "mode":"managed",
#    "type":"aws_ecr_lifecycle_policy",
#    "name":"repo_policy",
#    "index":0,
#    "provider_name":"registry.terraform.io/hashicorp/aws",
#    "schema_version":0,
#    "values":{
#       "id":"test-service-runx-app",
#       "policy":"{}",
#       "registry_id":"889760294590",
#       "repository":"test-service-runx-app"
#    },
#    "depends_on":[
#       "module.app.aws_ecr_repository.repo"
#    ]
# }
def _fetch_terraform_resources() -> List[Any]:
    out = nice_run(["terraform", "show", "-json"], check=True, capture_output=True)
    raw_data = out.stdout.decode("utf-8")
    data = json.loads(raw_data)

    root_module = data.get("values", {}).get("root_module", {})
    child_modules = root_module.get("child_modules", [])

    resources = root_module.get("resources", [])

    for child_module in child_modules:
        resources += child_module.get("resources", [])

    return resources


def _get_aws_region() -> str:
    tf_config = json.load(open(TF_FILE_PATH))
    return tf_config["provider"]["aws"]["region"]


def column_print(inspect_details: List[Any]) -> None:
    # Determine the width of each column (the length of the longest word + 1)
    longest_char_len_by_column = [0] * len(inspect_details[0])
    for resource_details in inspect_details:
        for column_idx, word in enumerate(resource_details):
            longest_char_len_by_column[column_idx] = max(
                len(word), longest_char_len_by_column[column_idx]
            )

    # Create each line of output one at a time.
    lines = []
    for resource_details in inspect_details:
        line = []
        for column_idx, word in enumerate(resource_details):
            line.append(word.ljust(longest_char_len_by_column[column_idx]))
        line_out = " ".join(line)
        lines.append(line_out)

    print("\n".join(lines))
