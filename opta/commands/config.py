import click
from click_didyoumean import DYMGroup

from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.exceptions import UserErrors
from opta.utils import logger


@click.group(cls=DYMGroup)
def config() -> None:
    """
    (Beta) Manage opta configurations.
    """
    pass


cloud_option = click.option(
    "--cloud",
    help="The cloud provider to use",
    required=True,
    type=click.Choice(["aws", "google", "azurerm"]),
)


@config.command()
@cloud_option
def view(cloud: str) -> None:
    """
    View the opta configuration file for a given cloud provider.
    Use the current cloud credentials to fetch the remote storage.

    Examples:

        - View opta configurations:

            opta config view --cloud aws
    """
    if cloud.lower() == "azurerm":
        raise UserErrors("Currently AzureRM isn't supported.")
    cloud_client: CloudClient = __get_cloud_client(cloud)
    detailed_config_map = cloud_client.get_detailed_config_map()
    if detailed_config_map:
        for bucket, detailed_configs in detailed_config_map.items():
            for config_name, actual_config in detailed_configs.items():
                logger.info(
                    f"# Bucket Name: {bucket}\n# Config Name: {config_name}\n{actual_config}\n\n"
                )


def __get_cloud_client(cloud: str) -> CloudClient:
    cloud_client: CloudClient
    if cloud.lower() == "aws":
        cloud_client = AWS  # type: ignore
    elif cloud.lower() == "google":
        cloud_client = GCP  # type: ignore
    elif cloud.lower() == "azurerm":
        cloud_client = Azure  # type: ignore

    return cloud_client  # type: ignore
