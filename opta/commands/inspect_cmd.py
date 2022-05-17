from typing import Any, Dict, List, Optional

import click

from opta.amplitude import amplitude_client
from opta.commands.apply import local_setup
from opta.constants import TF_FILE_PATH
from opta.core.generator import gen_all
from opta.core.terraform import fetch_terraform_state_resources
from opta.layer import Layer
from opta.pre_check import pre_check
from opta.resource import Resource
from opta.utils import check_opta_file_exists, column_print, deep_merge, json
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command(hidden=True)
@config_option
@env_option
@input_variable_option
@local_option
def inspect(
    config: str, env: Optional[str], local: Optional[bool], var: Dict[str, str],
) -> None:
    """Displays important resources and AWS/Datadog links to them"""

    pre_check()

    config = check_opta_file_exists(config)
    if local:
        config = local_setup(config)
    layer = Layer.load_from_yaml(config, env, input_variables=var)
    amplitude_client.send_event(
        amplitude_client.INSPECT_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)
    InspectCommand(layer).run()


class InspectCommand:
    def __init__(self, layer: Layer):
        self.layer = layer
        # Fetch the current terraform state
        self.terraform_state = fetch_terraform_state_resources(self.layer)

    def run(self) -> None:
        inspect_details = []
        target_resources = self._get_opta_config_terraform_resources()
        for resource in target_resources:
            if resource.inspect() == {}:
                continue
            # Make sure the resource exists in the current terraform state.
            if resource.address not in self.terraform_state:
                continue

            # Extract resource details to display as inspect output.
            inspected_resource_name = resource.inspect().get("name", "")
            inspected_resource_desc = resource.inspect().get("desc", "")
            inspected_resource_desc = inspected_resource_desc.replace("\n", " ")
            inspected_resource_template_url = resource.inspect().get("url", "")

            # Generate the resource url from the template.
            resource_state = self.terraform_state[resource.address]
            template_url_values = self._get_template_url_values(resource_state)
            inspected_resource_url = inspected_resource_template_url.format(
                **template_url_values
            )

            inspect_details.append(
                (inspected_resource_name, inspected_resource_desc, inspected_resource_url)
            )

        # Sort the inspected resources alphabetically
        inspect_details.sort()
        # TODO: Dedupe name and description of similar resources.
        # Add columm headers to the displayed output
        inspect_details.insert(0, ("NAME", "DESCRIPTION", "LINK"))
        column_print(inspect_details)

    def _get_opta_config_terraform_resources(self) -> List[Resource]:
        terraform_resources = []
        for module in self.layer.modules:
            terraform_resources += module.get_terraform_resources()

        return terraform_resources

    # Get values that may be needed to populate the resource's template URL.
    def _get_template_url_values(self, resource_state: dict) -> dict:
        template_url_values = {}

        # The template url may require the current AWS/GCP region.
        if self.layer.cloud == "aws":
            template_url_values["aws_region"] = self._get_aws_region()
        elif self.layer.cloud == "google":
            template_url_values["gcp_region"] = self._get_gcp_region()
            template_url_values["gcp_project"] = self._get_gcp_project()
        else:
            raise Exception(f"Currently can not handle cloud {self.layer.cloud}")

        # Get the resource properties from the terraform state, which
        # may be used to populate the template URL.
        for k, v in resource_state.items():
            template_url_values[k] = str(v)

        # Some inspect keys may require custom logic to fetch the values
        # for their template URL.
        if (
            resource_state.get("type") == "helm_release"
            and resource_state.get("name") == "k8s-service"
        ):
            k8s_metadata_values = self._get_k8s_metadata_values(resource_state)
            template_url_values = deep_merge(template_url_values, k8s_metadata_values)
        if resource_state.get("type") == "google_container_cluster":
            template_url_values["cluster_name"] = template_url_values["id"].split("/")[-1]
        return template_url_values

    def _get_k8s_metadata_values(self, resource_properties: dict) -> dict:
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

    def _get_aws_region(self) -> str:
        tf_config = self._read_tf_config()
        return tf_config["provider"]["aws"]["region"]

    def _get_gcp_region(self) -> str:
        tf_config = self._read_tf_config()
        return tf_config["provider"]["google"]["region"]

    def _get_gcp_project(self) -> str:
        tf_config = self._read_tf_config()
        return tf_config["provider"]["google"]["project"]

    def _read_tf_config(self) -> dict:
        with open(TF_FILE_PATH) as f:
            return json.load(f)
