# new-module-api

from opta.core.terraform2 import StateStore, StoreConfig
from opta.layer2 import Layer

from .aws import AWSProvider, S3Store
from .local import LocalStore
from .provider import CloudProvider


def cloud_provider_for_layer(layer: Layer) -> CloudProvider:
    """
    Returns a new CloudProvider based on the layer configuration.
    """

    cloud_id = layer.providers.cloud_id
    if not cloud_id:
        raise ValueError("No cloud provider configured")

    if config := layer.providers.aws:
        return AWSProvider(config)

    raise ValueError(f"Unknown cloud provider {cloud_id}")


def default_state_store_for_layer(layer: Layer, *, local: bool = False) -> StateStore:
    """
    Returns a new StateStore based on the layer configuration, or the local store if :local is True.
    """

    cloud_id = layer.providers.cloud_id
    if not cloud_id:
        raise ValueError("No cloud provider configured")

    org_name = layer.org_name
    if not org_name:
        # TODO: Can we pull this from the parent layer if it exists?
        raise ValueError("Unknown org name")

    config = StoreConfig(org_name=org_name, layer_name=layer.name)

    if local:
        return LocalStore(config)

    if cloud_config := layer.providers.aws:
        config.region = cloud_config.region

        return S3Store(config)

    raise ValueError(f"Unknown cloud provider {cloud_id}")
