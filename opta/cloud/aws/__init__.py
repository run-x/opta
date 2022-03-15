# new-module-api

from opta.cloud.registry import Registry
from opta.core.terraform2.state import StoreConfig

from .config import AWSProviderConfig
from .provider import AWSProvider
from .state import S3Store

__all__ = ["AWSProvider", "AWSProviderConfig", "S3Store"]


def register(registry: Registry) -> None:
    registry.register_provider("aws", AWSProvider, AWSProviderConfig)
    registry.register_state_store("s3", _make_store, config=AWSProviderConfig)
    registry.register_default_store("aws", "s3")


def _make_store(config: StoreConfig, provider_config: AWSProviderConfig) -> S3Store:
    config.region = provider_config.region

    return S3Store(config)
