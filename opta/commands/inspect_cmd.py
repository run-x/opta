import json
from typing import Any, List, Optional

import click
import yaml

from opta.constants import TF_FILE_PATH
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.resource import Resource
from opta.utils import column_print, deep_merge, is_tool


@click.command()
@click.option("--config", default="opta.yml", help="Opta config file", show_default=True)
@click.option("--env", default=None, help="The env to use when loading the config file")
def inspect(config: str, env: Optional[str]) -> None:
    """ Displays important resources and AWS/Datadog links to them """
    gen_all(config, env)
    Terraform.init()
    InspectCommand(config, env).run()


class InspectCommand:
    def __init__(self, config: str, env: Optional[str]):
        self.config = config
        self.env = env
        # Fetch the current terraform state
        self.terraform_state = self._fetch_terraform_state_resources()

    def run(self) -> None:
        # Make sure the user has the prerequisite CLI tools installed
        if not is_tool("terraform"):
            raise Exception("Please install terraform on your machine")

        inspect_details = []
        target_resources = self._get_opta_config_terraform_resources()
        for resource in target_resources:
            if resource.inspect is None:
                continue
            # Make sure the resource exists in the current terraform state.
            if resource.address not in self.terraform_state:
                continue

            # Extract resource details to display as inspect output.
            inspected_resource_name = resource.inspect.get("name", "")
            inspected_resource_desc = resource.inspect.get("desc", "")
            inspected_resource_desc = inspected_resource_desc.replace("\n", " ")
            inspected_resource_template_url = resource.inspect.get("url", "")

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
        out = nice_run(["terraform", "show", "-json"], check=True, capture_output=True)
        raw_data = out.stdout.decode("utf-8")
        data = json.loads(raw_data)

        root_module = data.get("values", {}).get("root_module", {})
        child_modules = root_module.get("child_modules", [])

        resources = root_module.get("resources", [])

        for child_module in child_modules:
            resources += child_module.get("resources", [])

        resources_dict = {}
        for resource in resources:
            address = resource.get("address")
            if address is None:
                continue

            # The terraform resource address may have "[0]" or "[#]" appending it, in
            # which case strip it out, so it's easier to match against the inspect key later.
            if "[" in address:
                address = address[0 : address.find("[")]

            resources_dict[address] = resource

        return resources_dict

    def _get_opta_config_terraform_resources(self) -> List[Resource]:
        conf = yaml.load(open(self.config), Loader=yaml.Loader)
        layer = Layer.load_from_dict(conf, self.env)

        terraform_resources = []
        for block in layer.blocks:
            for module in block.modules:
                terraform_resources += module.get_terraform_resources()

        return terraform_resources

    # Get values that may be needed to populate the resource's template URL.
    def _get_template_url_values(self, resource_state: dict) -> dict:
        template_url_values = {}

        # The template url may require the current AWS region.
        template_url_values["aws_region"] = self._get_aws_region()

        # Get the resource properties from the terraform state, which
        # may be used to populate the template URL.
        resource_properties = resource_state.get("values", {})
        for k, v in resource_properties.items():
            template_url_values[k] = str(v)

        # Some inspect keys may require custom logic to fetch the values
        # for their template URL.
        if (
            resource_state.get("type") == "helm_release"
            and resource_state.get("name") == "k8s-service"
        ):
            k8s_metadata_values = self._get_k8s_metadata_values(resource_properties)
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
