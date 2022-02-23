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
    "--cloud",
    help="The cloud provider to use",
    required=True,
    type=click.Choice(["aws", "google", "azurerm"]),
)


@config.command()
@cloud_option
def view(cloud: str) -> None:
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
    if cloud.lower() == "aws":
        cloud_client = AWS  # type: ignore
    elif cloud.lower() == "google":
        cloud_client = GCP  # type: ignore
    elif cloud.lower() == "azurerm":
        cloud_client = Azure  # type: ignore

    return cloud_client  # type: ignore
