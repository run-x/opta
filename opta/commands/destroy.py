import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import boto3
import click
from azure.storage.blob import ContainerClient
from botocore.config import Config
from colored import attr
from google.cloud import storage  # type: ignore
from google.cloud.exceptions import NotFound

from opta.amplitude import amplitude_client
from opta.commands.local_flag import _clean_tf_folder, _handle_local_flag
from opta.constants import TF_PLAN_PATH
from opta.core.azure import Azure
from opta.core.gcp import GCP
from opta.core.generator import gen_all
from opta.core.plan_displayer import PlanDisplayer
from opta.core.terraform import Terraform
from opta.error_constants import USER_ERROR_TF_LOCK
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.opta_lock import opta_acquire_lock, opta_release_lock
from opta.pre_check import pre_check
from opta.utils import check_opta_file_exists, logger
from opta.utils.clickoptions import (
    config_option,
    env_option,
    input_variable_option,
    local_option,
)


@click.command()
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    help="Automatically approve terraform plan.",
)
@click.option(
    "--detailed-plan",
    is_flag=True,
    default=False,
    help="Show full terraform plan in detail, not the opta provided summary",
)
@config_option
@env_option
@input_variable_option
@local_option
def destroy(
    config: str,
    env: Optional[str],
    auto_approve: bool,
    detailed_plan: bool,
    local: Optional[bool],
    var: Dict[str, str],
) -> None:
    """Destroy all opta resources from the current config

    To destroy an environment, you have to first destroy all the services first.

    Examples:

    opta destroy -c my-service.yaml --auto-approve

    opta destroy -c my-env.yaml --auto-approve
    """
    try:
        opta_acquire_lock()
        pre_check()
        logger.warning(
            "You are destroying your cloud infra state. DO NOT, I REPEAT, DO NOT do this as "
            "an attempt to debug a weird/errored apply. What you have created is not some ephemeral object that can be "
            "tossed arbitrarily (perhaps some day) and destroying unnecessarily just to reapply typically makes it "
            "worse. If you're doing this cause you are really trying to destroy the environment entirely, then that's"
            "perfectly fine-- if not then please reach out to the opta team in the slack workspace "
            "(https://slack.opta.dev) and I promise that they'll be happy to help debug."
        )

        config = check_opta_file_exists(config)
        if local:
            config, _ = _handle_local_flag(config, False)
            _clean_tf_folder()
        layer = Layer.load_from_yaml(config, env, input_variables=var)
        event_properties: Dict = layer.get_event_properties()
        amplitude_client.send_event(
            amplitude_client.DESTROY_EVENT, event_properties=event_properties,
        )
        layer.verify_cloud_credentials()
        layer.validate_required_path_dependencies()
        if not Terraform.download_state(layer):
            logger.info(
                "The opta state could not be found. This may happen if destroy ran successfully before."
            )
            return

        tf_lock_exists, _ = Terraform.tf_lock_details(layer)
        if tf_lock_exists:
            raise UserErrors(USER_ERROR_TF_LOCK)

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
            sleep_time = 5
            logger.info(
                f"{attr('bold')}Opta will now destroy the {attr('underlined')}{layer.name}{attr(0)}"
                f"{attr('bold')} layer.{attr(0)}\n"
                f"{attr('bold')}Sleeping for {attr('underlined')}{sleep_time} secs{attr(0)}"
                f"{attr('bold')}, press Ctrl+C to Abort.{attr(0)}"
            )
            time.sleep(sleep_time)
            tf_flags.append("-auto-approve")
        modules = Terraform.get_existing_modules(layer)
        layer.modules = [x for x in layer.modules if x.name in modules]
        gen_all(layer)
        Terraform.init(False, "-reconfigure", layer=layer)
        Terraform.refresh(layer)

        idx = len(layer.modules) - 1
        for module in reversed(layer.modules):
            try:
                module_address_prefix = f"-target=module.{module.name}"
                logger.info("Planning your changes (might take a minute)")
                Terraform.plan(
                    "-lock=false",
                    "-input=false",
                    "-destroy",
                    f"-out={TF_PLAN_PATH}",
                    layer=layer,
                    *list([module_address_prefix]),
                )
                PlanDisplayer.display(detailed_plan=detailed_plan)
                tf_flags = []
                if not auto_approve:
                    click.confirm(
                        "The above are the planned changes for your opta run. Do you approve?",
                        abort=True,
                    )
                else:
                    tf_flags.append("-auto-approve")
                Terraform.apply(layer, *tf_flags, TF_PLAN_PATH, no_init=True, quiet=False)
                layer.post_delete(idx)
                idx -= 1
            except Exception as e:
                raise e

        Terraform.delete_state_storage(layer)
    finally:
        opta_release_lock()


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
    elif layer.cloud == "helm":
        return []
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
    if layer.name in configs:
        configs.remove(layer.name)
    return configs


def _aws_get_configs(layer: "Layer") -> List[str]:
    # Opta configs for every layer are saved in the opta_config/ directory
    # in the state bucket.
    bucket_name = layer.state_storage()
    region = layer.root().providers["aws"]["region"]
    s3_config_dir = "opta_config/"
    s3_client = boto3.client("s3", config=Config(region_name=region))

    resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_config_dir)
    s3_config_paths = [obj["Key"] for obj in resp.get("Contents", [])]

    configs = [config_path[len(s3_config_dir) :] for config_path in s3_config_paths]
    if layer.name in configs:
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
        logger.warning(
            "Couldn't find the state bucket, must have already been destroyed in a previous destroy run"
        )
        return []
    blobs: List[storage.Blob] = list(
        gcs_client.list_blobs(bucket_object, prefix=gcs_config_dir)
    )
    configs = [blob.name[len(gcs_config_dir) :] for blob in blobs]
    if layer.name in configs:
        configs.remove(layer.name)
    return configs


def _local_get_configs(layer: "Layer") -> List[str]:
    local_config_dir = os.path.join(
        os.path.join(str(Path.home()), ".opta", "local", "opta_config")
    )
    configs = os.listdir(local_config_dir)
    if f"opta-{layer.org_name}-{layer.name}" in configs:
        configs.remove(f"opta-{layer.org_name}-{layer.name}")
    return configs
