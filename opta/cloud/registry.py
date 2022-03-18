# new-module-api

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type, TypeVar, Union, cast, overload

from opta.core.terraform2.state import StateStore, StoreConfig

from .provider import CloudProvider, ProviderConfig

# Using generic types here to avoid invariant type issues
T_ProviderConfig = TypeVar("T_ProviderConfig", bound="ProviderConfig")
T_CloudProvider = TypeVar("T_CloudProvider", bound="CloudProvider")
T_StateStore = TypeVar("T_StateStore", bound="StateStore")
FactoryWithConfig = Callable[[StoreConfig, T_ProviderConfig], T_StateStore]
FactoryNoConfig = Callable[[StoreConfig], T_StateStore]
ProviderFromConfig = Callable[[T_ProviderConfig], T_CloudProvider]


class Registry:
    """
    A registry contains registered cloud providers and state stores and can be used to generically
    instantiate such items
    """

    def __init__(self) -> None:
        self._providers: Dict[str, _ProviderRegistration] = {}
        self._state_stores: Dict[
            str, Union[_StoreRegistration, _StoreRegistrationWithConfig]
        ] = {}
        self._default_stores: Dict[str, str] = {}

    def get_default_store_id(self, cloud_id: str) -> str:
        try:
            return self._default_stores[cloud_id]
        except KeyError:
            raise ValueError(f"Unknown default store for cloud `{cloud_id}`")

    def get_provider(self, id: str, config: ProviderConfig) -> CloudProvider:
        try:
            registration = self._providers[id]
        except KeyError:
            raise ValueError(f"Unknown provider {id}")

        if not isinstance(config, registration.config_class):
            raise TypeError(
                f"Expected config for provider {id} be of type {registration.config_class.__qualname__}"
            )

        return registration.provider_factory(config)

    def get_state_store(
        self,
        id: str,
        config: StoreConfig,
        *,
        provider_config: Optional[ProviderConfig] = None,
    ) -> StateStore:
        try:
            registration = self._state_stores[id]
        except KeyError:
            raise ValueError(f"Unknown state store {id}")

        if isinstance(registration, _StoreRegistrationWithConfig):
            config_class = registration.config_id_and_class
            if not provider_config:
                raise ValueError(
                    f"Expected {config_class.__name__} to be provided for state store `{id}`"
                )

            if not isinstance(provider_config, config_class):
                raise TypeError(
                    f"Mismatch of type for provider config for state store `{id}`. Expected {config_class.__qualname__}, but got {provider_config.__class__.__qualname__}"
                )

            return registration.factory(config, provider_config)
        else:
            return registration.factory(config)

    def register_default_store(self, cloud_id: str, store_id: str) -> None:
        if cloud_id not in self._providers:
            raise ValueError(
                f"Cloud provider for `{cloud_id}` must be registered before registering default store"
            )

        if store_id not in self._state_stores:
            raise ValueError(
                f"State store `{store_id}` must be registered before registering default store"
            )

        if cloud_id in self._default_stores:
            raise ValueError(f"Default store for cloud `{cloud_id}` already registered")

        self._default_stores[cloud_id] = store_id

    def register_provider(
        self, id: str, factory: ProviderFromConfig, config: Type[ProviderConfig]
    ) -> None:
        if id in self._providers:
            raise ValueError(f"Provider `{id}` already registered")

        registration = _ProviderRegistration(
            config_class=config, provider_factory=factory
        )
        self._providers[id] = registration

    @overload
    def register_state_store(
        self, id: str, factory: FactoryWithConfig, *, config: Type[T_ProviderConfig]
    ) -> None:
        ...

    @overload
    def register_state_store(self, id: str, factory: FactoryNoConfig) -> None:
        ...

    def register_state_store(
        self,
        id: str,
        factory: Union[FactoryNoConfig, FactoryWithConfig],
        *,
        config: Optional[Type[T_ProviderConfig]] = None,
    ) -> None:
        if id in self._state_stores:
            raise ValueError(f"Store `{id}` already registered")

        if config:
            factory = cast(FactoryWithConfig, factory)
            self._state_stores[id] = _StoreRegistrationWithConfig(
                factory=factory, config_id_and_class=config
            )
        else:
            factory = cast(FactoryNoConfig, factory)
            self._state_stores[id] = _StoreRegistration(factory=factory)


# Data classes for holding registation info
@dataclass
class _ProviderRegistration:
    config_class: Type[ProviderConfig]
    provider_factory: ProviderFromConfig


@dataclass
class _StoreRegistration:
    factory: FactoryNoConfig


@dataclass
class _StoreRegistrationWithConfig:
    factory: FactoryWithConfig
    config_id_and_class: Type[ProviderConfig]


default = default_registry = Registry()
