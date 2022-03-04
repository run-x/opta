# new-module-api

import abc

from opta.core.terraform2 import TerraformFile


class CloudProvider(abc.ABC):
    @abc.abstractmethod
    def configure_terraform_file(self, file: TerraformFile) -> None:
        """
        Configures the terraform manifest as needed to use this cloud provider
        """
        ...
