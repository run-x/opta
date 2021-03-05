import json
from typing import Any, List, Optional

import click

from opta.amplitude import amplitude_client
from opta.constants import TF_FILE_PATH
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.resource import Resource
from opta.utils import column_print, deep_merge, is_tool


@click.command()
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
def inspect(config: str, env: Optional[str]) -> None:
    """ Displays important resources and AWS/Datadog links to them """
    amplitude_client.send_event(amplitude_client.INSPECT_EVENT)
    layer = Layer.load_from_yaml(config, env)
    gen_all(layer)
    InspectCommand(layer).run()


class InspectCommand:
    def __init__(self, layer: Layer):
        self.layer = layer
        Terraform.download_state(layer)
        # Fetch the current terraform state
        self.terraform_state = self._fetch_terraform_state_resources()

    def run(self) -> None:
        # Make sure the user has the prerequisite CLI tools installed
        if not is_tool("terraform"):
            raise Exception("Please install terraform on your machine")

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

    def _fetch_terraform_state_resources(self) -> dict:
        state = Terraform.get_state()

        resources = state.get("resources", [])

        resources_dict = {}
        for resource in resources:
            address = ".".join(
                [
                    resource.get("module", ""),
                    resource.get("type", ""),
                    resource.get("name", ""),
                ]
            )
            if address == "..":
                continue

            resources_dict[address] = resource["instances"][0]["attributes"]
            resources_dict[address]["module"] = resource.get("module", "")
            resources_dict[address]["type"] = resource.get("type", "")
            resources_dict[address]["name"] = resource.get("name", "")

        return resources_dict

    def _get_opta_config_terraform_resources(self) -> List[Resource]:
        terraform_resources = []
        for module in self.layer.modules:
            terraform_resources += module.get_terraform_resources()

        return terraform_resources

    # Get values that may be needed to populate the resource's template URL.
    def _get_template_url_values(self, resource_state: dict) -> dict:
        template_url_values = {}

        # The template url may require the current AWS region.
        template_url_values["aws_region"] = self._get_aws_region()

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
        tf_config = json.load(open(TF_FILE_PATH))
        return tf_config["provider"]["aws"]["region"]
