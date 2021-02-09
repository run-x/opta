import json
import os
import re
from typing import Any, List, Optional

import yaml

from opta.nice_subprocess import nice_run
from opta.utils import is_tool

INSPECT_CONFIG = "inspect.yml"


def inspect_cmd(configfile: str, env: Optional[str]) -> None:
    # Make sure the user has the prerequisite CLI tools installed
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")

    aws_region = _get_aws_region()

    inspect_config_file_path = os.path.join(os.path.dirname(__file__), INSPECT_CONFIG)
    inspect_config = yaml.load(open(inspect_config_file_path), Loader=yaml.Loader)
    inspected_resource_mappings = inspect_config["resources"]

    resources = _fetch_terraform_resources()
    inspect_details = []
    for resource in resources:
        resource_address = resource.get("address", "")
        if re.match(r".*\[[0-9]+\]", resource_address):
            continue

        for key in inspected_resource_mappings:
            # For example, the key may be "helm_release.k8s-service" and the full
            # resource address is "module.app.helm_release.k8s-service".
            if key in resource_address:
                resource_name = inspected_resource_mappings[key].get("name") or ""
                resource_description = inspected_resource_mappings[key].get("desc") or ""
                unformatted_resource_url = (
                    inspected_resource_mappings[key].get("url") or ""
                )

                resource_values = {"aws_region": aws_region}
                for k, v in resource.get("values").items():
                    resource_values[k] = str(v)

                resource_url = unformatted_resource_url.format(**resource_values)
                inspect_details.append(
                    (resource_name, resource_description, resource_url)
                )
                break

    inspect_details.sort()
    inspect_details.insert(0, ("NAME", "DESCRIPTION", "LINK"))
    column_print(inspect_details)


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
    tf_config = json.load(open("tmp.tf.json"))
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
