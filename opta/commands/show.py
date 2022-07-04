from typing import Optional

import click
from click_didyoumean import DYMGroup

from opta.core.aws import AWS
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.exceptions import AzureNotImplemented, UserErrors
from opta.layer import Layer
from opta.utils import logger
from opta.utils.clickoptions import config_option, env_option


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


@show.command()
@config_option
@env_option
def tf_state(config: str, env: Optional[str]) -> None:
    """
    Show terraform state
    """
    layer = Layer.load_from_yaml(config, env, strict_input_variables=False)
    cloud_client = layer.get_cloud_client()
    x = cloud_client.get_remote_state()
    print(x)


def __get_cloud_client(cloud: str, layer: Optional[Layer] = None) -> CloudClient:
    cloud_client: CloudClient
    if cloud.lower() == "aws":
        cloud_client = AWS(layer=layer)
    elif cloud.lower() == "google":
        cloud_client = GCP(layer=layer)
    else:
        raise UserErrors(f"Can't get client for cloud {cloud}")

    return cloud_client
