# new-module-api

from opta.core.terraform2 import StateStore, StoreConfig
from opta.layer2 import Layer

from .provider import CloudProvider
from .registry import Registry, default_registry


def cloud_provider_for_layer(layer: Layer) -> CloudProvider:
    """
    Returns a new CloudProvider based on the layer configuration.
    """

    cloud_id, config = layer.providers.cloud_id_and_config

    if not cloud_id:
        raise ValueError("No cloud provider configured")

    if not config:
        # If cloud_id is not None, config is also not None,
        # but mypy isn't able to detect that situation,
        # so we have to validate it ourselves
        raise AssertionError("unexpected config is None")

    return default_registry.get_provider(cloud_id, config)


def default_state_store_for_layer(layer: Layer, *, local: bool = False) -> StateStore:
    """
    Returns a new StateStore based on the layer configuration, or the local store if :local is True.
    """

    cloud_id, cloud_config = layer.providers.cloud_id_and_config

    if not cloud_id:
        raise ValueError("No cloud provider configured")

    org_name = layer.org_name
    if not org_name:
        # TODO: Pull this from the parent layer if it exists, once we add support for layer-peering
        raise ValueError("Unknown org name")

    store_config = StoreConfig(org_name=org_name, layer_name=layer.name)

    if local:
        store_id = "local"
    else:
        store_id = default_registry.get_default_store_id(cloud_id)

    store = default_registry.get_state_store(
        store_id, store_config, provider_config=cloud_config
    )

    return store


def _register_clouds(registry: Registry) -> None:
    from . import aws, local

    aws.register(registry)
    local.register(registry)


_register_clouds(default_registry)
