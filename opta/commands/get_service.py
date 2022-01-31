import click

from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.core.local import Local
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists, logger


@click.command()
@click.option("-c", "--config", default="opta.yaml", help="Opta environment config file")
@click.option("-n", "--service-name", default=None, help="Name of dependent service")
@click.option("-o", "--output-file", default=None, help="Local file to download service configuration")
def get_service(config: str, service_name: str, output_file: str) -> None:
    """

    """
    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, None)
    cloud_client: CloudClient
    if layer.cloud == "aws":
        cloud_client = AWS(layer)
    elif layer.cloud == "google":
        cloud_client = GCP(layer)
    elif layer.cloud == "azurerm":
        cloud_client = Azure(layer)
    elif layer.cloud == "local":
        raise Exception(f"Configurations would be present on the same system.")
    else:
        raise Exception(f"Cannot handle upload config for cloud {layer.cloud}")

    child_service_names = cloud_client.list_child_config_names()
    if service_name is None:
        print("Following are the dependent service names")
        for index, child_service_name in enumerate(child_service_names):
            print(f"{index + 1}.\t{child_service_name}")
        return

    if service_name not in child_service_names:
        raise UserErrors("Service name invalid")

    requested_service_configuration = cloud_client.get_configuration_details(service_name)
    if output_file is None:
        print(requested_service_configuration)
        return

