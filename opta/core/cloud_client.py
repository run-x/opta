from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    def list_child_config_names(self) -> List[str]:
        pass

    @abstractmethod
    def get_configuration_details(self, config_name: str) -> Dict[str, Any]:
        pass

    @classmethod
    def get_config_map(cls) -> Dict[str, List[str]]:
        pass

    @classmethod
    def get_detailed_config_map(cls, environment: Optional[str] = None):
        pass
