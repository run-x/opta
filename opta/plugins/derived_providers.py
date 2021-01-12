from typing import Any, Dict, Optional

from opta.utils import deep_merge, hydrate


class DerivedProviders:
    def __init__(self, layer: Any, is_parent: bool):
        self.layer = layer
        self.is_parent = is_parent

    def gen_tf(self, block_idx: Optional[int] = None) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        if self.layer is None:
            return ret
        if block_idx is None:
            block_idx = len(self.layer.blocks)
        blocks = self.layer.blocks if self.is_parent else self.layer.blocks[:block_idx]
        for b in blocks:
            for m in b.modules:
                if "providers" in m.desc:
                    hydration = {
                        "layer_name": self.layer.meta["name"],
                        "state_storage": self.layer.state_storage(),
                        "module_source": "data.terraform_remote_state.parent.outputs"
                        if self.is_parent
                        else f"module.{m.key}",
                    }
                    ret = deep_merge(hydrate(m.desc["providers"], hydration), ret)
        return ret
