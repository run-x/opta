from typing import TYPE_CHECKING, List, Optional

from modules.base import AWSIamAssembler, ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsDynamodbProcessor(ModuleProcessor, AWSIamAssembler):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AwsDynamodbProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        attributes: List[dict] = self.module.data["attributes"]
        range_key: Optional[str] = self.module.data.get("range_key", None)
        hash_key: str = self.module.data["hash_key"]
        valid_keys: List[str] = (
            [hash_key, range_key] if range_key is not None else [hash_key]
        )
        for attribute in attributes:
            if attribute["name"] not in valid_keys:
                raise UserErrors(
                    "All attributes must be either a hash key or range key (global secondary index support "
                    "coming soon. If you wish to set a non-indexed attribute you must do it from your app code "
                    "(you should have no problem)."
                )
        super(AwsDynamodbProcessor, self).process(module_idx)
