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

name_option = click.option(
    "-n", "--name", help="The name of the configuration", required=False
)

environment_option = click.option(
    "-e", "--environment", help="The name of the environment", required=False
)


@config.command(name="list")
@cloud_option
@environment_option
def list_command(cloud: str, environment: Optional[str]) -> None:
    if environment:
        logger.info("Environment option is a feature in progress.")
    cloud_client: CloudClient = __get_cloud_client(cloud)
    config_map = cloud_client.get_config_map()
    if config_map:
        logger.info(config_map)


@config.command()
@cloud_option
@environment_option
@name_option
def view(cloud: str, environment: Optional[str], name: Optional[str]) -> None:
    if environment or name:
        logger.info("Environment/Name option is a feature in progress.")
    cloud_client: CloudClient = __get_cloud_client(cloud)
    detailed_config_map = cloud_client.get_detailed_config_map()
    if detailed_config_map:
        for bucket, detailed_configs in detailed_config_map.items():
            for config_name, actual_config in detailed_configs.items():
                logger.info(
                    f"Bucket Name: {bucket}\nConfig Name: {config_name}\nActual Config:\n{actual_config}"
                )


def __get_cloud_client(cloud: str) -> CloudClient:
    cloud_client: CloudClient
    if cloud == "aws":
        cloud_client = AWS  # type: ignore
    elif cloud == "google":
        cloud_client = GCP  # type: ignore
    elif cloud == "azurerm":
        cloud_client = Azure  # type: ignore

    return cloud_client  # type: ignore
