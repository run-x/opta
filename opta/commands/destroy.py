from typing import List, Optional

import boto3
import click
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound

from opta.amplitude import amplitude_client
from opta.core.gcp import GCP
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.layer import Layer
from opta.utils import fmt_msg, logger, yaml


@click.command(hidden=True)
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
@click.option(
    "-e", "--env", default=None, help="The env to use when loading the config file."
)
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    help="Automatically approve terraform plan.",
)
def destroy(config: str, env: Optional[str], auto_approve: bool) -> None:
    """Destroy all opta resources from the current config"""
    amplitude_client.send_event(amplitude_client.DESTROY_EVENT)
    layer = Layer.load_from_yaml(config, env)
    if not Terraform.download_state(layer):
        logger.info(
            "The opta state could not be found. This may happen if destroy ran successfully before."
        )
        return

    # Any child layers should be destroyed first before the current layer.
    children_layers = _fetch_children_layers(layer)
    destroy_order = [*children_layers, layer]

    tf_flags: List[str] = []
    if auto_approve:
        # Note that for ci, you can just do "yes | opta destroy --auto-approve"
        click.confirm(
            fmt_msg(
                f"""
                Are you REALLY sure you want to run destroy with auto-approve?
                ~Please make sure *{layer.name}* is the correct opta config.
                """
            ),
            abort=True,
        )
        tf_flags.append("-auto-approve")

    for layer in destroy_order:
        gen_all(layer)
        Terraform.init("-reconfigure")
        Terraform.destroy_all(layer, *tf_flags)


# Fetch all the children layers of the current layer.
def _fetch_children_layers(layer: "Layer") -> List["Layer"]:
    # Only environment layers have children (service) layers.
    # If the current layer has a parent, it is *not* an environment layer.
    if layer.parent is not None:
        return []

    # Download all the opta config files in the bucket
    bucket_name = layer.state_storage()
    if layer.cloud == "aws":
        opta_configs = _aws_download_all_opta_configs(bucket_name)
    elif layer.cloud == "google":
        opta_configs = _gcp_download_all_opta_configs(bucket_name)
    else:
        raise Exception(f"Not handling deletion for cloud {layer.cloud}")
    # Keep track of children layers as we find them.
    children_layers = []
    for config_path in opta_configs:
        config_data = yaml.load(open(config_path))

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
def _aws_download_all_opta_configs(bucket_name: str) -> List[str]:
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
        local_config_path = f"tmp.opta.{config_name}"
        with open(local_config_path, "wb") as f:
            s3_client.download_fileobj(bucket_name, config_path, f)

        configs.append(local_config_path)

    return configs


def _gcp_download_all_opta_configs(bucket_name: str) -> List[str]:
    gcs_config_dir = "opta_config/"
    credentials, project_id = GCP.get_credentials()
    gcs_client = storage.Client(project=project_id, credentials=credentials)
    try:
        bucket_object = gcs_client.get_bucket(bucket_name)
    except NotFound:
        logger.warn(
            "Couldn't find the state bucket, must have already been destroyed in a previous destroy run"
        )
        return []
    blobs: List[storage.Blob] = list(
        gcs_client.list_blobs(bucket_object, prefix=gcs_config_dir)
    )
    configs: List[str] = []
    for blob in blobs:
        configs.append(blob.download_as_bytes().decode("utf-8"))
    return configs
