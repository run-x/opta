from typing import Optional

import click

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.layer import Layer
from opta.meister import time as meister_time
from opta.utils import check_opta_file_exists, json


@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yaml", help="Opta config file")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
def output(config: str, env: Optional[str],) -> None:
    """Print TF outputs"""
    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, env)
    amplitude_client.send_event(
        amplitude_client.VIEW_OUTPUT_EVENT,
        event_properties={"org_name": layer.org_name, "layer_name": layer.name},
    )
    layer.verify_cloud_credentials()
    gen_all(layer)
    outputs = get_terraform_outputs(layer)
    # Adding extra outputs
    if layer.cloud == "aws":
        outputs = _load_extra_aws_outputs(outputs)
    elif layer.cloud == "google":
        outputs = _load_extra_gcp_outputs(outputs)
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)


@meister_time
def _load_extra_aws_outputs(current_outputs: dict) -> dict:
    if "parent.load_balancer_raw_dns" in current_outputs:
        current_outputs["load_balancer_raw_dns"] = current_outputs[
            "parent.load_balancer_raw_dns"
        ]
        del current_outputs["parent.load_balancer_raw_dns"]
    return current_outputs


@meister_time
def _load_extra_gcp_outputs(current_outputs: dict) -> dict:
    if "parent.load_balancer_raw_ip" in current_outputs:
        current_outputs["load_balancer_raw_ip"] = current_outputs[
            "parent.load_balancer_raw_ip"
        ]
        del current_outputs["parent.load_balancer_raw_ip"]
    return current_outputs
