from threading import Thread
from typing import List, Optional, Set

import boto3
import click
from botocore.config import Config
from packaging import version

from opta.amplitude import amplitude_client
from opta.constants import MAX_TERRAFORM_VERSION, MIN_TERRAFORM_VERSION, TF_PLAN_PATH
from opta.core.aws import AWS
from opta.core.gcp import GCP
from opta.core.generator import gen, gen_opta_resource_tags
from opta.core.kubernetes import (
    configure_kubectl,
    current_image_tag,
    get_cluster_name,
    tail_module_log,
    tail_namespace_events,
)
from opta.core.terraform import Terraform
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import fmt_msg, is_tool, logger


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
    "--max-module", default=None, type=int, help="Max module to process", hidden=True
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
    "--auto-approve",
    is_flag=True,
    default=False,
    help="Automatically approve terraform plan.",
)
def apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: Optional[str],
    test: bool,
    auto_approve: bool,
) -> None:
    """Initialize your environment or service to match the config file"""
    _apply(config, env, refresh, max_module, image_tag, test, auto_approve)


def _check_terraform_version() -> None:
    if not is_tool("terraform"):
        raise UserErrors("Please install terraform on your machine")
    current_version = Terraform.get_version()
    if version.parse(current_version) < version.parse(MIN_TERRAFORM_VERSION):
        raise UserErrors(
            f"Invalid terraform version {current_version}-- must be at least {MIN_TERRAFORM_VERSION}"
        )
    if version.parse(current_version) >= version.parse(MAX_TERRAFORM_VERSION):
        raise UserErrors(
            f"Invalid terraform version {current_version}-- must be less than  {MAX_TERRAFORM_VERSION}"
        )


def _apply(
    config: str,
    env: Optional[str],
    refresh: bool,
    max_module: Optional[int],
    image_tag: Optional[str],
    test: bool,
    auto_approve: bool,
) -> None:
    _check_terraform_version()
    amplitude_client.send_event(amplitude_client.START_GEN_EVENT)
    layer = Layer.load_from_yaml(config, env)

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
    if layer.cloud == "aws":
        AWS(layer).upload_opta_config(config)
    elif layer.cloud == "google":
        GCP(layer).upload_opta_config(config)
    else:
        raise Exception(f"Cannot handle upload config for cloud {layer.cloud}")

    service_modules = (
        layer.get_module_by_type("k8s-service")
        if layer.cloud == "aws"
        else layer.get_module_by_type("gcp-k8s-service")
    )

    if len(service_modules) > 0 and (get_cluster_name(layer.root()) is not None):
        configure_kubectl(layer)

        for service_module in service_modules:
            current_tag = current_image_tag(layer)
            if (
                current_tag is not None
                and image_tag is None
                and service_module.data.get("image", "") == "AUTO"
                and not test
            ):
                if click.confirm(
                    f"WARNING There is an existing deployment (tag={current_tag}) and the pods will be killed as you "
                    f"did not specify an image tag. Would you like to keep the existing deployment alive? (y/n)",
                ):
                    image_tag = current_tag

    layer.variables["image_tag"] = image_tag

    existing_modules: Set[str] = set()
    first_loop = True
    for module_idx, current_modules, total_block_count in gen(layer):
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
        targets = list(map(lambda x: f"-target=module.{x}", sorted(configured_modules)))
        if test:
            Terraform.plan("-lock=false", *targets)
            print("Plan ran successfully, not applying since this is a test.")
        else:
            amplitude_client.send_event(
                amplitude_client.APPLY_EVENT, event_properties={"module_idx": module_idx}
            )
            logger.info("Planning your changes (might take a minute)")
            Terraform.plan(
                "-lock=false",
                "-input=false",
                f"-out={TF_PLAN_PATH}",
                *targets,
                quiet=True,
            )
            Terraform.show(TF_PLAN_PATH)

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
            if len(service_modules) != 0 and get_cluster_name(layer.root()) is not None:
                service_module = service_modules[0]
                # Tailing logs
                logger.info(
                    f"Identified deployment for kubernetes service module {service_module.name}, tailing logs now."
                )
                new_thread = Thread(
                    target=tail_module_log,
                    args=(layer, service_module.name, 10, 2),
                    daemon=True,
                )
                # Tailing events
                new_thread.start()
                new_thread = Thread(
                    target=tail_namespace_events, args=(layer, 0, 1), daemon=True,
                )
                new_thread.start()

            tf_flags: List[str] = []
            if auto_approve:
                tf_flags.append("-auto-approve")
            try:
                Terraform.apply(layer, *tf_flags, TF_PLAN_PATH, no_init=True, quiet=False)
            except Exception as e:
                layer.post_hook(module_idx, e)
                raise e
            else:
                layer.post_hook(module_idx, None)
            logger.info("Opta updates complete!")


# Fetch the AZs of a region with boto3
def _fetch_availability_zones(aws_region: str) -> List[str]:
    client = boto3.client("ec2", config=Config(region_name=aws_region))
    resp = client.describe_availability_zones(
        Filters=[{"Name": "zone-type", "Values": ["availability-zone"]}]
    )
    return list(map(lambda az: az["ZoneName"], resp["AvailabilityZones"]))
