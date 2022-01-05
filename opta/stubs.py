from typing import Protocol, Type, TypeVar

T = TypeVar("T", bound="_Stub")

class _Stub:
    @classmethod
    def from_dict(cls: T, raw: dict) -> T:
        pass

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
