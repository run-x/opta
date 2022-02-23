# new-module-api

"""
Quick "stub" classes that are added to provided needed functionality but will need to be expanded before the module API is complete
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Type, TypeVar

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


class AWSProvider(Provider):
    def __init__(self, region: str) -> None:
        self.region = region
        self.account_ids: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, raw: dict) -> AWSProvider:

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
        self.aws: Optional[AWSProvider] = None

    @classmethod
    def from_dict(cls, raw: dict) -> ProviderConfig:
        type_mapping: Dict[str, Type[Provider]] = {
            "aws": AWSProvider,
        }

        providers = cls()

        for type, config in raw.items():
            try:
                provider_cls = type_mapping[type]
            except KeyError:
                raise ValueError(f"Unknown provider type {type}")

            provider = provider_cls.from_dict(config)

            setattr(providers, type, provider)

        return providers
