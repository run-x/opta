from typing import Dict, List, Optional, Protocol, Type, TypeVar

T = TypeVar("T", bound="_Stub")

class _Stub:
    def __init__(self) -> None:
        self._raw = None

    @classmethod
    def from_dict(cls: T, raw: dict) -> T:
        stub = cls()
        stub._raw = raw

        return stub


T_FromDict = TypeVar("T_FromDict", bound="FromDict")

class FromDict(Protocol):
    @classmethod
    def from_dict(cls: T_FromDict, raw: dict) -> T_FromDict:
        ...

def from_dict(cls: Type[T_FromDict], data: dict, key: str) -> T_FromDict:
    return [
        cls.from_dict(raw) for raw in data.get(key, [])
    ]

class Environment(_Stub):
    pass

class Provider(_Stub):
    pass

class AWSProvider(Provider):
    def __init__(self):
        self.region: Optional[str] = None
        self.account_ids: List[str] = []

    @classmethod
    def from_dict(cls, raw: dict) -> "AWSProvider":
        p = cls()
        p.region = raw.get("region")
        account_ids = raw.get("account_id", [])
        if isinstance(account_ids, str):
            p.account_ids = [account_ids]
        else:
            p.account_ids = account_ids

        return p


class ProviderConfig:
    def __init__(self):
        self.aws: Provider = None

    @classmethod
    def from_dict(cls, raw: dict) -> "ProviderConfig":
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
