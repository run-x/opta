# new-module-api

import abc
from typing import Type, TypeVar

from opta.core.terraform2 import TerraformFile

T_ProviderConfig = TypeVar("T_ProviderConfig", bound="ProviderConfig")


class CloudProvider(abc.ABC):
    @abc.abstractmethod
    def configure_terraform_file(self, file: TerraformFile) -> None:
        """
        Configures the terraform manifest as needed to use this cloud provider
        """
        ...


class ProviderConfig:
    """
    The configuration of a provider, as specified in an opta layer file
    """

    @classmethod
    def from_dict(cls: Type[T_ProviderConfig], raw: dict) -> T_ProviderConfig:
        raise NotImplementedError("must be implemented by subclasses")
