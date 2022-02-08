import os.path

import click

from opta.core.aws import AWS
from opta.core.azure import Azure
from opta.core.cloud_client import CloudClient
from opta.core.gcp import GCP
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import check_opta_file_exists, logger


@click.command()
@click.option("-c", "--config", default="opta.yaml", help="Opta environment config file")
@click.option("-n", "--service-name", default=None, help="Name of dependent service")
@click.option(
    "-o",
    "--output-file",
    default=None,
    help="Local file to download service configuration",
)
def get_service(config: str, service_name: str, output_file: str) -> None:
    """
    Get the Dependent Service configuration for a given Environment.

    Examples:

    - View all services:

        opta get-service -c opta.yaml

    - View a specific service:

        opta get-service -c opta.yaml -n <service_name>

    - Download a specific service:

        opta get-service -c opta.yaml -n <service_name> -o <output_file>
    """
    config = check_opta_file_exists(config)
    layer = Layer.load_from_yaml(config, None)
    abs_output_file = get_abs_path(output_file) if output_file is not None else None
    overwrite_existing_file(abs_output_file)
    layer.verify_cloud_credentials()
    cloud_client: CloudClient
    if layer.cloud == "aws":
        cloud_client = AWS(layer)
    elif layer.cloud == "google":
        cloud_client = GCP(layer)
    elif layer.cloud == "azurerm":
        cloud_client = Azure(layer)
    elif layer.cloud == "local":
        raise Exception("Configurations would be present on the same system.")
    else:
        raise Exception(f"Cannot handle upload config for cloud {layer.cloud}")

    child_service_names = cloud_client.list_child_config_names()

    if not child_service_names:
        logger.info("No child services found.")
        return

    if service_name is None:
        logger.info("Following are the dependent service names")
        for child_service_name in child_service_names:
            logger.info(f"  - {child_service_name}")
        return

    if service_name not in child_service_names:
        raise UserErrors("Service name invalid")

    requested_service_configuration = cloud_client.get_configuration_details(service_name)
    if abs_output_file is None:
        logger.info(requested_service_configuration)
        return

    with open(abs_output_file, "w") as f:
        f.write(requested_service_configuration)    # type: ignore


def get_abs_path(file_path: str) -> str:
    directory_path = os.path.dirname(file_path)
    if not os.path.isdir(os.path.abspath(directory_path)):
        raise UserErrors("Incorrect output file path")
    return os.path.abspath(file_path)


def overwrite_existing_file(file_path: str) -> None:
    if os.path.isfile(file_path):
        click.confirm(
            "File with such name already exists. Do you want to overwrite it?", abort=True
        )
