from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig


class CloudClient:
    def __init__(self, layer: "Layer"):
        self.layer = layer

    def get_remote_config(self) -> Optional["StructuredConfig"]:
        pass

    def upload_opta_config(self) -> None:
        pass

    def delete_opta_config(self) -> None:
        pass

    def delete_remote_state(self) -> None:
        pass

    def get_terraform_lock_id(self) -> str:
        pass
