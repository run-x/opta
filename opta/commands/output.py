import json
from typing import Optional

import click

from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.nice_subprocess import nice_run
from opta.utils import deep_merge


def get_terraform_outputs() -> dict:
    """ Fetch terraform outputs from existing TF file """
    Terraform.init()
    outputs = _fetch_current_outputs()
    outputs = deep_merge(outputs, _fetch_parent_outputs())

    return outputs


def _fetch_current_outputs() -> dict:
    outputs_raw = nice_run(
        ["terraform", "output", "-json"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    outputs = json.loads(outputs_raw)
    cleaned_outputs = {}
    for k, v in outputs.items():
        cleaned_outputs[k] = v.get("value")
    return cleaned_outputs


def _fetch_parent_outputs() -> dict:
    # Fetch the terraform state
    out = nice_run(["terraform", "show", "-json"], check=True, capture_output=True)
    raw_data = out.stdout.decode("utf-8")
    data = json.loads(raw_data)

    # Fetch any parent remote states
    root_module = data.get("values", {}).get("root_module", {})
    resources = root_module.get("resources", [])
    parent_states = [
        resource
        for resource in resources
        if resource.get("type") == "terraform_remote_state"
    ]

    # Grab all outputs from each remote state and save it.
    parent_state_outputs = {}
    for parent in parent_states:
        parent_outputs = parent.get("values", {}).get("outputs", {})
        for k, v in parent_outputs.items():
            parent_name = parent.get("name")
            output_name = f"{parent_name}.{k}"
            parent_state_outputs[output_name] = v

    return parent_state_outputs


@click.command(hidden=True)
@click.option("--configfile", default="opta.yml", help="Opta config file")
@click.option("--env", default=None, help="The env to use when loading the config file")
@click.option(
    "--include-parent",
    is_flag=True,
    default=False,
    help="Also fetch outputs from the env (parent) layer",
)
@click.option(
    "--force-init",
    is_flag=True,
    default=False,
    help="Force regenerate opta setup files, instead of using cache",
)
def output(
    configfile: str, env: Optional[str], include_parent: bool, force_init: bool,
) -> None:
    """ Print TF outputs """
    gen_all(configfile, env)
    outputs = get_terraform_outputs()
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)
