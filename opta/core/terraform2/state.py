# new-module-api

from __future__ import annotations

import abc
from copy import copy
from dataclasses import dataclass
from typing import Optional, Union

from opta.core.terraform2.terraform_file import TerraformFile
from opta.utils import json


@dataclass
class StoreConfig:
    org_name: str
    layer_name: str
    region: Optional[
        str
    ] = None  # TODO: Should this be moved to a "cloud specific" field?


class StateStore(abc.ABC):
    # TODO: Storage for opta-config as well
    def __init__(self, config: StoreConfig) -> None:
        config = copy(config)
        self._validate_config(config)

        self.config = config

    @abc.abstractmethod
    def configure_storage(self) -> None:
        """
        Configures the storage location and ensures configuration is up to date.
        Implementations must be idempotent and backwards compatible.
        """
        ...

    @abc.abstractmethod
    def configure_terraform_file(self, tf: TerraformFile) -> None:
        """
        Configure the terraform manifest to use this state storage
        """
        ...

    @abc.abstractmethod
    def is_storage_configured(self) -> bool:
        """
        Returns True if the state storage is fully set up and configured, false otherwise
        """
        ...

    @abc.abstractmethod
    def read_raw(self) -> str:
        """
        Return the raw state data as a string (not parsed)
        """
        ...

    def read(self) -> StateData:
        """
        Returns the parsed state data
        """

        raw = self.read_raw()
        return StateData(raw)

    @classmethod
    def _validate_config(cls, config: StoreConfig) -> None:
        """
        Can be overridden in subclasses to add validation to the config passed
        to the constructor.
        """
        pass


class StateNotFoundError(Exception):
    pass


class StateData:
    def __init__(self, raw: Union[str, dict]) -> None:
        parsed: dict
        if isinstance(raw, str):
            parsed = json.loads(raw)
        else:
            parsed = raw

        self._raw = parsed

    @property
    def raw(self) -> dict:
        return self._raw

    # TODO: Implement get_existing_modules from opta.core.terraform.Terraform.get_existing_modules
