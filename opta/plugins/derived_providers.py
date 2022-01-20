from typing import Any, Dict, Optional

from opta.utils import deep_merge, hydrate


class DerivedProviders:
    def __init__(self, layer: Any, is_parent: bool):
        self.layer = layer
        self.is_parent = is_parent

    def gen_tf(
        self, base_hydration: dict, module_idx: Optional[int] = None
    ) -> Dict[Any, Any]:
        ret: Dict[Any, Any] = {}
        if self.layer is None:
            return ret
        if module_idx is None:
            module_idx = len(self.layer.modules)
        for m in self.layer.modules[:module_idx]:
            if m.desc["output_providers"] != {}:
                hydration = deep_merge(
                    {
                        "layer_name": self.layer.name,
                        "state_storage": self.layer.state_storage(),
                        "module_source": "data.terraform_remote_state.parent.outputs"
                        if self.is_parent
                        else f"module.{m.name}",
                    },
                    base_hydration,
                )
                hydrated_provider, formatter = hydrate(
                    {"provider": m.desc["output_providers"]}, hydration
                )
                formatter.is_valid()
                ret = deep_merge(hydrated_provider, ret)
            if m.desc["output_data"] != {}:
                hydration = deep_merge(
                    {
                        "layer_name": self.layer.name,
                        "state_storage": self.layer.state_storage(),
                        "module_source": "data.terraform_remote_state.parent.outputs"
                        if self.is_parent
                        else f"module.{m.name}",
                    },
                    base_hydration,
                )
                output_hydration, formatter = hydrate(
                    {"data": m.desc["output_data"]}, hydration
                )
                formatter.is_valid()
                ret = deep_merge(output_hydration, ret)
        return ret
