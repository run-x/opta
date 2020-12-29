from typing import Any, Iterable, Mapping


class BaseModule:
    def __init__(self, meta: Mapping[Any, Any], key: str, data: Mapping[Any, Any]):
        pass

    def gen_blocks(self) -> Iterable[Mapping[Any, Any]]:
        pass


class EnvModule(BaseModule):
    def gen_env_blocks(self) -> Iterable[Mapping[Any, Any]]:
        pass


class Module(BaseModule):
    pass
