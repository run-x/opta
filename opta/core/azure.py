from typing import TYPE_CHECKING, Any, Optional

from azure.identity import DefaultAzureCredential

if TYPE_CHECKING:
    from opta.layer import Layer


class Azure:
    project_id: Optional[str] = None

    def __init__(self, layer: "Layer"):
        self.layer = layer

    @classmethod
    def get_credentials(cls) -> Any:
        return DefaultAzureCredential()
