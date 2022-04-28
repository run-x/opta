import click
from click_didyoumean import DYMGroup

from opta.core.aws import AWS
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.exceptions import AzureNotImplemented
from opta.utils import logger


@click.group(cls=DYMGroup)
def show() -> None:
    """
    Show opta related project details such as configurations and many more to be added soon.
    """
    pass


cloud_option = click.option(
    "--cloud",
    help="The cloud provider to use",
    required=True,
    type=click.Choice(["aws", "google", "azurerm"]),
)


@show.command()
@cloud_option
def config(cloud: str) -> None:
    """
    View the opta configuration file for a given cloud provider

    Use the current cloud credentials to fetch the remote opta config file
    """
    if cloud.lower() == "azurerm":
        raise AzureNotImplemented(
            "Currently AzureRM isn't supported for this command, as Opta's AzureRM support is in Beta"
        )
    cloud_client: CloudClient = __get_cloud_client(cloud)
    detailed_config_map = cloud_client.get_all_remote_configs()
    if detailed_config_map:
        for bucket, detailed_configs in detailed_config_map.items():
            for config_name, actual_config in detailed_configs.items():
                logger.info(
                    f"# Bucket Name: {bucket}\n# Config Name: {config_name}\n{actual_config['original_spec']}\n"
                )


def __get_cloud_client(cloud: str) -> CloudClient:
    cloud_client: CloudClient
    if cloud.lower() == "aws":
        cloud_client = AWS()
    elif cloud.lower() == "google":
        cloud_client = GCP()

    return cloud_client
