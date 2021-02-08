from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class ModuleProcessor:
    def __init__(self, module: "Module", layer: "Layer") -> None:
        self.layer = layer
        self.module = module

    def process(self, block_idx: int) -> None:
        raise Exception("Needs to be defined by subclasses")
