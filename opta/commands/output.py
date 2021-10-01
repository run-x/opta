import json
from typing import Optional

import boto3
import click
from botocore.config import Config
from mypy_boto3_elbv2 import ElasticLoadBalancingv2Client

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.terraform import get_terraform_outputs
from opta.layer import Layer
from opta.utils import check_opta_file_exists, logger


@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yml", help="Opta config file")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file"
)
def output(config: str, env: Optional[str],) -> None:
    """ Print TF outputs """

    check_opta_file_exists(config)
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
        outputs = _load_extra_aws_outputs(layer, outputs)
    elif layer.cloud == "google":
        outputs = _load_extra_gcp_outputs(layer, outputs)
    outputs_formatted = json.dumps(outputs, indent=4)
    print(outputs_formatted)


def _load_extra_aws_outputs(layer: Layer, current_outputs: dict) -> dict:
    providers = layer.gen_providers(0)
    region = providers["provider"]["aws"]["region"]
    client: ElasticLoadBalancingv2Client = boto3.client(
        "elbv2", config=Config(region_name=region)
    )
    marker = ""
    while True:
        output = client.describe_load_balancers(Marker=marker)
        marker = output.get("NextMarker", "")
        load_balancers = output.get("LoadBalancers", [])
        current_arns = [x["LoadBalancerArn"] for x in load_balancers]
        arn_to_lb = {x["LoadBalancerArn"]: x for x in load_balancers}
        tag_descriptions = client.describe_tags(ResourceArns=current_arns)[
            "TagDescriptions"
        ]
        cluster_name = f"opta-{layer.root().name}"
        for idx, tag_description in enumerate(tag_descriptions):
            tag_dict = {d["Key"]: d["Value"] for d in tag_description["Tags"]}

            if (
                tag_dict.get(f"kubernetes.io/cluster/{cluster_name}") == "owned"
                and tag_dict.get("kubernetes.io/service-name")
                == "ingress-nginx/ingress-nginx-controller"
            ):
                current_outputs["load_balancer_raw_dns"] = arn_to_lb[
                    tag_description["ResourceArn"]
                ]["DNSName"]
                return current_outputs

        if marker == "":
            break
    logger.info(
        "Could not find load balancer for current environment/service. Please re-run opta apply on the environment file."
    )
    return current_outputs


def _load_extra_gcp_outputs(layer: Layer, current_outputs: dict) -> dict:
    if "parent.load_balancer_raw_ip" in current_outputs:
        current_outputs["load_balancer_raw_ip"] = current_outputs[
            "parent.load_balancer_raw_ip"
        ]
        del current_outputs["parent.load_balancer_raw_ip"]
    return current_outputs
