from typing import Optional
import click
from click_didyoumean import DYMGroup

from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP

from opta.utils import logger


@click.group(cls=DYMGroup)
def config() -> None:
    pass


cloud_option = click.option(
    "-c",
    "--cloud",
    help="The cloud provider to use",
    required=True,
    type=click.Choice(["aws", "google", "azurerm"]),
)

name_option = click.option("-n", "--name", help="The name of the configuration", required=False)

environment_option = click.option("-e", "--environment", help="The name of the environment", required=False)


@config.command(name="list")
@cloud_option
@environment_option
def list_command(cloud: str, environment: Optional[str]) -> None:
    cloud_client: CloudClient
    if cloud == "aws":
        cloud_client = AWS
    elif cloud == "google":
        cloud_client = GCP
    elif cloud == "azurerm":
        cloud_client = Azure
    config_map = cloud_client.get_config_map()
    requested_config_map = None
    if environment:
        for bucket_name, configs in config_map.items():
            if environment in configs:
                requested_config_map = {bucket_name: configs}
                break
        logger.info(requested_config_map)
    else:
        logger.info(config_map)


@config.command()
@cloud_option
@environment_option
@name_option
def view(cloud: str, environment: Optional[str], name: Optional[str]) -> None:
    cloud_client: CloudClient
    if cloud == "aws":
        cloud_client = AWS
    elif cloud == "google":
        cloud_client = GCP
    elif cloud == "azurerm":
        cloud_client = Azure
    detailed_config_map = cloud_client.get_detailed_config_map()