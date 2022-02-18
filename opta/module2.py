# new-module-api

from __future__ import annotations

import copy
from typing import Any, Dict, Optional


class Module:
    """
    New type for module instances (as specified in opta files)
    """

    type: str
    input: Dict[str, Any]
    processor: Optional[ModuleProcessor]

    # TODO: Handle aliases on `type` (e.g. `base` instead of `aws-base`)

    def __init__(self) -> None:
        self.input = {}
        self._alias: Optional[str] = None
        self.processor = None

    def __repr__(self) -> str:
        args = {
            "type": self.type,
            "input": self.input,
        }

        if self.alias != self.type:
            args["alias"] = self.alias

        printed_args = ", ".join(
            f"{key}={repr(value)}" for key, value in args.items() if value
        )

        return f"Module({printed_args})"

    @property
    def alias(self) -> str:
        return self._alias or self.type

    @alias.setter
    def alias(self, value: Optional[str]) -> None:
        if value:
            self._alias = value
        else:
            self._alias = None

    @property
    def proxy(self) -> ModuleProxy:
        return ModuleProxy(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> Module:
        module = cls()
        module.type = raw["type"]

        if "alias" in raw:
            module.alias = raw["alias"]

        input = copy.deepcopy(raw)
        input.pop("type", ...)
        input.pop("alias", ...)
        module.input = input

        return module

    def to_dict(self) -> Dict[str, Any]:
        raw: Dict[str, Any] = {
            "type": self.type,
            "alias": self.alias,
        }

        if self.input:
            raw["input"] = self.input

        return raw

    def pre_terraform_plan(self, vars: Dict[str, Any]) -> None:
        if self.processor:
            self.processor.pre_terraform_plan(vars)

    def pre_terraform_apply(self) -> None:
        if self.processor:
            self.processor.pre_terraform_apply()

    def post_terraform_apply(self) -> None:
        if self.processor:
            self.processor.post_terraform_apply()


class ModuleProxy:
    def __init__(self, source: Module) -> None:
        self.__source = source
        self.__input: Optional[Dict[str, Any]] = None

    @property
    def type(self) -> str:
        return self.__source.type

    @property
    def alias(self) -> str:
        return self.__source.alias

    @property
    def input(self) -> Dict[str, Any]:
        if self.__input is None:
            self.__input = copy.deepcopy(self.__source.input)

        return self.__input


class ModuleProcessor:
    def __init__(self, module: ModuleProxy) -> None:
        self.module = module

    def pre_terraform_plan(self, vars: Dict[str, Any]) -> None:
        """
        Can modify terraform values
        """
        pass

    def pre_terraform_apply(self) -> None:
        """
        Can inspect the terraform plan
        """
        pass

    def post_terraform_apply(self) -> None:
        pass


Module2 = Module
ModuleProcessor2 = ModuleProcessor
