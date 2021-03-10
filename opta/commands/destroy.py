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
    children_layers = _fetch_children_layers(layer)
    destroy_order = [*children_layers, layer]
    for layer in destroy_order:
        gen_all(layer)
        Terraform.init()
        Terraform.destroy()


def _fetch_children_layers(layer: "Layer") -> List["Layer"]:
    if layer.parent is not None:
        return []

    s3_bucket_name = layer.state_storage()
    opta_configs = _fetch_all_opta_configs(s3_bucket_name)

    children_layers = []
    for config_path in opta_configs:
        config_data = yaml.load(open(config_path), Loader=yaml.Loader)

        if "environments" not in config_data:
            continue

        envs = [env["name"] for env in config_data["environments"]]
        for env in envs:
            child_layer = Layer.load_from_yaml(config_path, env)
            if child_layer.parent and child_layer.parent.name == layer.name:
                children_layers.append(child_layer)

    return children_layers


def _fetch_all_opta_configs(bucket_name: str) -> List[str]:
    s3_config_dir = "opta_config/"
    s3_client = boto3.client("s3")

    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_config_dir)
    if resp["KeyCount"] == 0:
        return []
    s3_config_paths = [obj["Key"] for obj in resp["Contents"]]

    configs = []
    for config_path in s3_config_paths:
        layer_name = config_path[len(s3_config_dir) :]
        local_config_path = f"opta-tmp-{layer_name}"
        with open(local_config_path, "wb") as f:
            s3_client.download_fileobj(bucket_name, config_path, f)

        configs.append(local_config_path)

    return configs
