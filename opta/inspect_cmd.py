import json
from typing import Any, List

from opta.constants import REGISTRY, TF_FILE_PATH
from opta.nice_subprocess import nice_run
from opta.utils import all_substrings, column_print, deep_merge, is_tool


def inspect_cmd() -> None:
    # Make sure the user has the prerequisite CLI tools installed
    if not is_tool("terraform"):
        raise Exception("Please install terraform on your machine")

    # Read the registry for the inspected resources
    inspected_resource_mappings = REGISTRY["inspected_resources"]

    # Fetch the terraform state
    resources = _fetch_terraform_resources()
    inspect_details = []
    for resource in resources:
        # Every terraform resource has an "address", and this is what
        # the inspect config matches on.
        # Ex. "module.app.helm_release.k8s-service"
        resource_address = resource.get("address", "")

        # If the terraform resource address has ".data." in it, then
        # it's not the actual ref to the created resource, in which case, skip.
        if ".data." in resource_address:
            continue

        # The terraform resource address may have "[0]" or "[#]" appending it, in
        # which case strip it out, so it's easier to match against the inspect key later.
        if "[" in resource_address:
            resource_address = resource_address[0 : resource_address.find("[")]

        for inspect_key in inspected_resource_mappings:
            # The inspect key should be a substring of the full resource address.
            # Ex. "helm_release.k8s-service" or "aws_docdb_cluster"
            # Using all_substrings() to match only on full, not partial, words.
            if inspect_key in all_substrings(resource_address, "."):
                resource_name = inspected_resource_mappings[inspect_key].get("name") or ""
                resource_desc = inspected_resource_mappings[inspect_key].get("desc") or ""
                resource_template_url = (
                    inspected_resource_mappings[inspect_key].get("url") or ""
                )

                # Generate the resource url from the template.
                template_url_values = _get_template_url_values(resource, inspect_key)
                # print(template_url_values)
                resource_url = resource_template_url.format(**template_url_values)

                inspect_details.append((resource_name, resource_desc, resource_url))

                # Only match a resource to its first matching inspect key.
                break

    # Sort the inspected resources alphabetically
    inspect_details.sort()
    # TODO: Dedupe name and description of similar resources.
    # Add columm headers to the displayed output
    inspect_details.insert(0, ("NAME", "DESCRIPTION", "LINK"))
    column_print(inspect_details)


# Get values that may be needed to populate the resource's template URL.
def _get_template_url_values(resource_state: dict, inspect_key: str) -> dict:
    template_url_values = {}

    # The template url may require the current AWS region.
    template_url_values["aws_region"] = _get_aws_region()

    # Get the resource properties from the terraform state, which
    # may be used to populate the template URL.
    resource_properties = resource_state.get("values", {})
    for k, v in resource_properties.items():
        template_url_values[k] = str(v)

    # Some inspect keys may require custom logic to fetch the values
    # for their template URL.
    if inspect_key == "helm_release.k8s-service":
        k8s_metadata_values = _get_k8s_metadata_values(resource_properties)
        template_url_values = deep_merge(template_url_values, k8s_metadata_values)

    return template_url_values


def _get_k8s_metadata_values(resource_properties: dict) -> dict:
    if "metadata" not in resource_properties:
        return {}

    k8s_values: Any = {}
    for chart in resource_properties["metadata"]:
        chart_values = json.loads(chart.get("values", "{}"))
        k8s_values = deep_merge(k8s_values, chart_values)

    values: Any = {}
    for k, v in k8s_values.items():
        values[f"k8s-{k}"] = v

    return values


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
