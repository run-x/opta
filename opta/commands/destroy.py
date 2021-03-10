from typing import List, Optional

import boto3
import click
import yaml

from opta.amplitude import amplitude_client
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
def destroy(config: str, env: Optional[str]) -> None:
    """Destroy all opta resources from the current config"""
    amplitude_client.send_event(amplitude_client.DESTROY_EVENT)

    layer = Layer.load_from_yaml(config, env)

    # Any child layers should be destroyed first before the current layer.
    children_layers = _fetch_children_layers(layer)
    destroy_order = [*children_layers, layer]

    for layer in destroy_order:
        gen_all(layer)
        Terraform.init("-reconfigure")
        Terraform.destroy()


# Fetch all the children layers of the current layer.
def _fetch_children_layers(layer: "Layer") -> List["Layer"]:
    # Only environment layers have children (service) layers.
    # If the current layer has a parent, it is *not* an environment layer.
    if layer.parent is not None:
        return []

    # Download all the opta config files in the bucket
    s3_bucket_name = layer.state_storage()
    opta_configs = _download_all_opta_configs(s3_bucket_name)

    # Keep track of children layers as we find them.
    children_layers = []
    for config_path in opta_configs:
        config_data = yaml.load(open(config_path), Loader=yaml.Loader)

        # If the config has no 'environments' field, then it cannot be
        # a child/service layer.
        if "environments" not in config_data:
            continue

        # Try all the possible environments for this config
        envs = [env["name"] for env in config_data["environments"]]
        for env in envs:
            # Load the child layer, and check if its parent is the current layer.
            child_layer = Layer.load_from_yaml(config_path, env)
            if child_layer.parent and child_layer.parent.name == layer.name:
                children_layers.append(child_layer)

    return children_layers


# Download all the opta config files from the specified bucket and return
# a list of temporary file paths to access them.
def _download_all_opta_configs(bucket_name: str) -> List[str]:
    # Opta configs for every layer are saved in the opta_config/ directory
    # in the state bucket.
    s3_config_dir = "opta_config/"
    s3_client = boto3.client("s3")

    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_config_dir)
    s3_config_paths = [obj["Key"] for obj in resp.get("Contents", [])]

    configs = []
    # Download every opta config file and write each to a temp file.
    for config_path in s3_config_paths:
        config_name = config_path[len(s3_config_dir) :]
        local_config_path = f"opta-tmp-{config_name}"
        with open(local_config_path, "wb") as f:
            s3_client.download_fileobj(bucket_name, config_path, f)

        configs.append(local_config_path)

    return configs
