import datetime
import os
from pathlib import Path
from subprocess import CalledProcessError  # nosec
from threading import Thread
from typing import Dict, List, Optional, Set

import boto3
import click
import pytz
import semver
from botocore.config import Config
from botocore.exceptions import ClientError

from opta.amplitude import amplitude_client
from opta.cleanup_files import cleanup_files
from opta.commands.local_flag import _clean_tf_folder, _handle_local_flag
from opta.constants import DEV_VERSION, TF_PLAN_PATH, VERSION
from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.core.generator import gen, gen_opta_resource_tags
from opta.core.kubernetes import get_cluster_name, tail_module_log, tail_namespace_events
from opta.core.local import Local
from opta.core.plan_displayer import PlanDisplayer
from opta.core.terraform import Terraform, get_terraform_outputs
from opta.error_constants import USER_ERROR_TF_LOCK
from opta.exceptions import MissingState, UserErrors
from opta.layer import Layer, StructuredConfig
from opta.pre_check import pre_check
from opta.utils import check_opta_file_exists, fmt_msg, logger


@click.command()
@click.option(
    "-c", "--config", default="opta.yml", help="Opta config file", show_default=True
)
@click.option(
    "-e",
    "--env",
    default=None,
    help="The env to use when loading the config file",
    show_default=True,
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Run from first block, regardless of current state",
    hidden=True,
)
@click.option(
    "--image-tag",
    default=None,
    type=str,
    help="If this handles a service, it's the image tag you wanna deploy",
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Run tf plan, but don't lock state file",
    hidden=True,
)
@click.option(
    "--local",
    is_flag=True,
    default=False,
    help="""Run the service locally on a local Kubernetes cluster for development and testing,  irrespective of the environment specified inside the opta service yaml file""",
    hidden=False,
)
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
def apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    local: bool,
    image_tag: Optional[str],
    test: bool,
    auto_approve: bool,
    detailed_plan: bool,
) -> None:
    """Initialize your environment or service to match the config file

    Examples:

    opta apply -c my_config.yaml --auto-approve

    opta apply -c my_config.yaml --image-tag=v1
    """
    config = check_opta_file_exists(config)
    _apply(
        config,
        env,
        refresh,
        local,
        image_tag,
        test,
        auto_approve,
        detailed_plan=detailed_plan,
    )


def _apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    local: bool,
    image_tag: Optional[str],
    test: bool,
    auto_approve: bool,
    image_digest: Optional[str] = None,
    stdout_logs: bool = True,
    detailed_plan: bool = False,
) -> None:
    pre_check()
    _clean_tf_folder()
    if local:
        adjusted_config = _handle_local_flag(config, test)
        if adjusted_config != config:  # Only do this for service opta files
            config = adjusted_config  # Config for service
            localopta_envfile = os.path.join(
                Path.home(), ".opta", "local", "localopta.yml"
            )
            _apply(
                config=localopta_envfile,
                auto_approve=True,
                local=False,
                env="",
                refresh=True,
                image_tag=image_tag,
                test=test,
                detailed_plan=True,
            )
            _clean_tf_folder()

    layer = Layer.load_from_yaml(config, env)
    layer.verify_cloud_credentials()
    layer.validate_required_path_dependencies()

    if Terraform.download_state(layer):
        tf_lock_exists, _ = Terraform.tf_lock_details(layer)
        if tf_lock_exists:
            raise UserErrors(USER_ERROR_TF_LOCK)
    _verify_parent_layer(layer)

    event_properties: Dict = layer.get_event_properties()
    amplitude_client.send_event(
        amplitude_client.START_GEN_EVENT, event_properties=event_properties,
    )

    # We need a region with at least 3 AZs for leader election during failover.
    # Also EKS historically had problems with regions that have fewer than 3 AZs.
    if layer.cloud == "aws":
        providers = layer.gen_providers(0)["provider"]
        aws_region = providers["aws"]["region"]
        azs = _fetch_availability_zones(aws_region)
        if len(azs) < 3:
            raise UserErrors(
                fmt_msg(
                    f"""
                    Opta requires a region with at least *3* availability zones.
                    ~You configured {aws_region}, which only has the availability zones: {azs}.
                    ~Please choose a different region.
                    """
                )
            )

    Terraform.create_state_storage(layer)
    gen_opta_resource_tags(layer)
    cloud_client: CloudClient
    if layer.cloud == "aws":
        cloud_client = AWS(layer)
    elif layer.cloud == "google":
        cloud_client = GCP(layer)
    elif layer.cloud == "azurerm":
        cloud_client = Azure(layer)
    elif layer.cloud == "local":
        if local:  # boolean passed via cli
            pass
        cloud_client = Local(layer)
    else:
        raise Exception(f"Cannot handle upload config for cloud {layer.cloud}")

    previous_config: Optional[StructuredConfig] = cloud_client.get_remote_config()
    if previous_config is not None and "opta_version" in previous_config:
        old_opta_version = previous_config["opta_version"]
        if (
            old_opta_version not in [DEV_VERSION, ""]
            and VERSION not in [DEV_VERSION, ""]
            and semver.VersionInfo.parse(VERSION.strip("v")).compare(
                old_opta_version.strip("v")
            )
            < 0
        ):
            raise UserErrors(
                f"ou're trying to run an older version of opta (last run was at {previous_config['date']} with version {old_opta_version}). Please update to the latest version and try again!"
            )

    try:
        existing_modules: Set[str] = set()
        first_loop = True
        for module_idx, current_modules, total_block_count in gen(
            layer, previous_config, image_tag, image_digest, test, True
        ):
            if first_loop:
                # This is set during the first iteration, since the tf file must exist.
                existing_modules = Terraform.get_existing_modules(layer)
                first_loop = False
            configured_modules = set([x.name for x in current_modules]) - {
                "runx"
            }  # Ignore runx module
            is_last_module = module_idx == total_block_count - 1
            has_new_modules = not configured_modules.issubset(existing_modules)
            if not is_last_module and not has_new_modules and not refresh:
                continue
            if is_last_module:
                untouched_modules = existing_modules - configured_modules
                configured_modules = configured_modules.union(untouched_modules)

            layer.pre_hook(module_idx)
            if layer.cloud == "local":
                if is_last_module:
                    targets = []
            else:
                targets = list(
                    map(lambda x: f"-target=module.{x}", sorted(configured_modules))
                )
            if test:
                Terraform.plan("-lock=false", *targets, layer=layer)
                print("Plan ran successfully, not applying since this is a test.")
            else:
                current_properties = event_properties.copy()
                current_properties["module_idx"] = module_idx
                amplitude_client.send_event(
                    amplitude_client.APPLY_EVENT, event_properties=current_properties,
                )
                logger.info("Planning your changes (might take a minute)")

                try:
                    Terraform.plan(
                        "-lock=false",
                        "-input=false",
                        f"-out={TF_PLAN_PATH}",
                        layer=layer,
                        *targets,
                        quiet=True,
                    )
                except CalledProcessError as e:
                    logger.error((e.stderr or b"").decode("utf-8"))
                    raise e
                PlanDisplayer.display(detailed_plan=detailed_plan)

                if not auto_approve:
                    click.confirm(
                        "The above are the planned changes for your opta run. Do you approve?",
                        abort=True,
                    )
                logger.info("Applying your changes (might take a minute)")
                service_modules = (
                    layer.get_module_by_type("k8s-service", module_idx)
                    if layer.cloud == "aws"
                    else layer.get_module_by_type("gcp-k8s-service", module_idx)
                )
                if (
                    len(service_modules) != 0
                    and get_cluster_name(layer.root()) is not None
                    and stdout_logs
                ):
                    service_module = service_modules[0]
                    # Tailing logs
                    logger.info(
                        f"Identified deployment for kubernetes service module {service_module.name}, tailing logs now."
                    )
                    new_thread = Thread(
                        target=tail_module_log,
                        args=(
                            layer,
                            service_module.name,
                            10,
                            datetime.datetime.utcnow().replace(tzinfo=pytz.UTC),
                            2,
                        ),
                        daemon=True,
                    )
                    # Tailing events
                    new_thread.start()
                    new_thread = Thread(
                        target=tail_namespace_events,
                        args=(
                            layer,
                            datetime.datetime.utcnow().replace(tzinfo=pytz.UTC),
                            1,
                        ),
                        daemon=True,
                    )
                    new_thread.start()

                tf_flags: List[str] = []
                if auto_approve:
                    tf_flags.append("-auto-approve")
                try:
                    Terraform.apply(
                        layer, *tf_flags, TF_PLAN_PATH, no_init=True, quiet=False
                    )
                except Exception as e:
                    layer.post_hook(module_idx, e)
                    raise e
                else:
                    layer.post_hook(module_idx, None)
                cloud_client.upload_opta_config()
                logger.info("Opta updates complete!")
    except Exception as e:
        event_properties["success"] = False
        event_properties["error_name"] = e.__class__.__name__
        raise e
    else:
        event_properties["success"] = True
    finally:
        amplitude_client.send_event(
            amplitude_client.FINISH_GEN_EVENT, event_properties=event_properties,
        )


# Fetch the AZs of a region with boto3
def _fetch_availability_zones(aws_region: str) -> List[str]:
    client = boto3.client("ec2", config=Config(region_name=aws_region))
    azs: List[str] = []
    resp = client.describe_availability_zones(
        Filters=[{"Name": "zone-type", "Values": ["availability-zone"]}]
    )
    azs = list(map(lambda az: az["ZoneName"], resp["AvailabilityZones"]))
    return azs


# Verify whether the parent layer exists or not
def _verify_parent_layer(layer: Layer) -> None:
    if layer.parent is None:
        return
    try:
        get_terraform_outputs(layer.parent)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            raise UserErrors(
                f"We were unable to fetch Environment details for the Env {layer.parent.name}, on your AWS account (opta needs this to store state). "
                "Usually, it means that your AWS account has insufficient permissions. "
                "Please fix these issues and try again!"
            )
    except MissingState as e:
        click.confirm(
            f"Failed to get the Environment state {e.args[0]} "
            "Usually, this means that the Environment mentioned in configuration file does not exist. \n"
            f"Would you like to create your environment using {layer.parent.path}?",
            abort=True,
        )
        _apply(
            layer.parent.path,
            env=None,
            refresh=False,
            local=False,
            image_tag=None,
            test=False,
            auto_approve=False,
        )
        cleanup_files()
