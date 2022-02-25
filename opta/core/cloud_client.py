from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class CloudClient(ABC):
    def __init__(self, layer: "Layer"):
        self.layer = layer

    @abstractmethod
    def get_remote_config(self) -> Optional["StructuredConfig"]:
        pass

    @abstractmethod
    def upload_opta_config(self) -> None:
        pass

    @abstractmethod
    def delete_opta_config(self) -> None:
        pass

    @abstractmethod
    def delete_remote_state(self) -> None:
        pass

    @abstractmethod
    def get_terraform_lock_id(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def cluster_exist(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def set_kube_config(self) -> None:
        raise NotImplementedError()
