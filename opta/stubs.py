# new-module-api

"""
Quick "stub" classes that are added to provided needed functionality but will need to be expanded before the module API is complete
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Set, Type, TypeVar

from opta.exceptions import UserErrors

T = TypeVar("T", bound="_Stub")


class _Stub:
    def __init__(self) -> None:
        self._raw: dict = {}

    @classmethod
    def from_dict(cls: Type[T], raw: dict) -> T:
        stub = cls()
        stub._raw = raw

        return stub


T_FromDict = TypeVar("T_FromDict", bound="FromDict")


class FromDict(Protocol):
    @classmethod
    def from_dict(cls: Type[T_FromDict], raw: dict) -> T_FromDict:
        ...


def from_dict(cls: Type[T_FromDict], data: dict, key: str) -> List[T_FromDict]:
    return [cls.from_dict(raw) for raw in data.get(key, [])]


class Environment(_Stub):
    pass


class Provider(_Stub):
    pass


class AWSProviderConfig(Provider):
    def __init__(self, region: str) -> None:
        self.region = region
        self.account_ids: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, raw: dict) -> AWSProviderConfig:

        try:
            region = raw["region"]
        except KeyError:
            raise UserErrors("AWS region must be provided when using the AWS provider")

        p = cls(region)

        account_ids = raw.get("account_id")
        if isinstance(account_ids, list):
            p.account_ids = [str(id) for id in account_ids]
        elif account_ids:
            p.account_ids = [str(account_ids)]

        return p


class ProviderConfig:
    def __init__(self) -> None:
        self.aws: Optional[AWSProviderConfig] = None

    @property
    def cloud_id(self) -> Optional[str]:
        """
        The cloud id/type of the configured cloud provider, if any.
        """
        configured_providers = self._configured_providers

        if not configured_providers:
            return None

        return next(iter(configured_providers))

    @classmethod
    def from_dict(cls, raw: dict) -> ProviderConfig:
        type_mapping = cls._cloud_type_mapping()

        providers = cls()

        for type, config in raw.items():
            try:
                provider_cls = type_mapping[type]
            except KeyError:
                raise ValueError(f"Unknown provider type {type}")

            provider = provider_cls.from_dict(config)

            setattr(providers, type, provider)

        if len(providers._configured_providers) > 1:
            raise ValueError("Cannot configure multiple cloud providers")

        return providers

    @property
    def _configured_providers(self) -> Set[str]:
        return {id for id in self._cloud_type_mapping() if getattr(self, id) is not None}

    @classmethod
    def _cloud_type_mapping(cls) -> Dict[str, Type[Provider]]:
        # TODO: In 3.9+, this method can be a @property (https://docs.python.org/3.9/library/functions.html#classmethod)
        return {
            "aws": AWSProviderConfig,
        }
