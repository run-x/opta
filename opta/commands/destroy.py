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
        Terraform.destroy()


def _fetch_children_layers(layer: "Layer") -> List["Layer"]:
    if layer.parent is not None:
        return []

    s3_bucket_name = layer.state_storage()
    opta_configs = _fetch_all_opta_configs(s3_bucket_name)

    children_layers = []
    for config_path, config_data in opta_configs.items():
        if "environments" not in config_data:
            continue

        envs = [env["name"] for env in config_data["environments"]]
        for env in envs:
            child_layer = Layer.load_from_yaml(config_path, env)
            if child_layer.parent == layer:
                children_layers.append(child_layer)

    return children_layers


def _fetch_all_opta_configs(bucket_name: str) -> dict:
    s3_config_dir = "opta_config/"
    s3_client = boto3.client("s3")

    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_config_dir)
    if resp["KeyCount"] == 0:
        return {}
    s3_config_paths = [obj["Key"] for obj in resp["Contents"]]

    configs = {}
    for config_path in s3_config_paths:
        layer_name = config_path[len(s3_config_dir) :]
        tmp_local_config_path = f"opta-tmp-{layer_name}"
        with open(tmp_local_config_path, "wb") as f:
            s3_client.download_fileobj(bucket_name, config_path, f)

        config_data = yaml.load(open(layer_name), Loader=yaml.Loader)
        configs[tmp_local_config_path] = config_data

    return configs


# def _calculate_destroy_order(layer_name: str, env: Optional[str], all_configs: dict):
#     parent_to_child_layer_mapping = {}
#     for layer_name, config_data in all_configs.items():
#         if "environments" not in config_data:
#             continue

#         parent_layers = [env["name"] for env in config_data["environments"]]
#         for parent_layer_name in parent_layers:
#             if parent_layer_name not in parent_to_child_layer_mapping:
#                 parent_to_child_layer_mapping[parent_layer_name] = []
#             parent_to_child_layer_mapping[parent_layer_name].append(layer_name)


#     order_of_layers_destroyed = []
#     def dfs(parent):
#         if parent in parent_to_child_layer_mapping:
#             children = parent_to_child_layer_mapping[parent]
#             for child in children:
#                 dfs(child)

#         order_of_layers_destroyed.append(layer_name)

#     dfs((layer_name, env))
#     return order_of_layers_destroyed
