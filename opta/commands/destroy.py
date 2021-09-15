from typing import List, Optional
import os
from pathlib import Path
import boto3
import click
from azure.storage.blob import ContainerClient
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound

from opta.amplitude import amplitude_client
from opta.core.azure import Azure
from opta.core.gcp import GCP
from opta.core.generator import gen_all
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists, fmt_msg, logger


@click.command()
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

    check_opta_file_exists(config)
    amplitude_client.send_event(amplitude_client.DESTROY_EVENT)
    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    if not Terraform.download_state(layer):
        logger.info(
            "The opta state could not be found. This may happen if destroy ran successfully before."
        )
        return

    # Any child layers should be destroyed first before the current layer.
    children_layers = _fetch_children_layers(layer)
    if children_layers:
        # TODO: ideally we can just automatically destroy them but it's
        # complicated...
        logger.error(
            "Found the following services that depend on this environment. Please run `opta destroy` on them first!\n"
            + "\n".join(children_layers)
        )
        raise UserErrors("Dependant services found!")

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

    gen_all(layer)
    Terraform.init("-reconfigure", layer=layer)
    logger.info(f"Destroying {layer.name}")
    Terraform.destroy_all(layer, *tf_flags)


# Fetch all the children layers of the current layer.
def _fetch_children_layers(layer: "Layer") -> List[str]:
    # Only environment layers have children (service) layers.
    # If the current layer has a parent, it is *not* an environment layer.
    if layer.parent is not None:
        return []

    # Download all the opta config files in the bucket
    if layer.cloud == "aws":
        opta_configs = _aws_get_configs(layer)
    elif layer.cloud == "google":
        opta_configs = _gcp_get_configs(layer)
    elif layer.cloud == "azurerm":
        opta_configs = _azure_get_configs(layer)
    elif layer.cloud == "local":
        opta_configs = _local_get_configs(layer)
    else:
        raise Exception(f"Not handling deletion for cloud {layer.cloud}")

    return opta_configs


# Get the names for all services for this environment based on the bucket file paths
def _azure_get_configs(layer: "Layer") -> List[str]:
    providers = layer.gen_providers(0)
    credentials = Azure.get_credentials()
    storage_account_name = providers["terraform"]["backend"]["azurerm"][
        "storage_account_name"
    ]
    container_name = providers["terraform"]["backend"]["azurerm"]["container_name"]
    storage_client = ContainerClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        container_name=container_name,
        credential=credentials,
    )
    prefix = "opta_config/"
    blobs = storage_client.list_blobs(name_starts_with=prefix)
    configs = [blob.name[len(prefix) :] for blob in blobs]
    configs.remove(layer.name)
    return configs


def _aws_get_configs(layer: "Layer") -> List[str]:
    # Opta configs for every layer are saved in the opta_config/ directory
    # in the state bucket.
    bucket_name = layer.state_storage()
    s3_config_dir = "opta_config/"
    s3_client = boto3.client("s3")

    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_config_dir)
    s3_config_paths = [obj["Key"] for obj in resp.get("Contents", [])]

    configs = [config_path[len(s3_config_dir) :] for config_path in s3_config_paths]
    configs.remove(layer.name)
    return configs


def _gcp_get_configs(layer: "Layer") -> List[str]:
    bucket_name = layer.state_storage()
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
    configs = [blob.name[len(gcs_config_dir) :] for blob in blobs]
    configs.remove(layer.name)
    return configs

def _local_get_configs(layer: "Layer") -> List[str]:
    local_config_dir =  local_dir = os.path.join(os.path.join(str(Path.home()), ".opta", "local","opta_config"))
    configs =  os.listdir(local_config_dir)
    configs.remove(layer.name)
    return configs
