from typing import Any, Dict

from opta.constants import REGISTRY


class BaseModule:
    def __init__(
        self,
        layer_name: str,
        key: str,
        data: Dict[Any, Any],
        parent_layer: Any = None,
    ):
        self.key = key
        self.desc = REGISTRY["modules"][data["type"]]
        self.name = f"{layer_name}-{self.key}"
        self.parent_layer = parent_layer
        self.data = data

    def gen_tf(self) -> Dict[Any, Any]:
        module_blk = {"module": {self.key: {"source": self.desc["location"]}}}
        for k, v in self.desc["variables"].items():
            if k in self.data:
                module_blk["module"][self.key][k] = self.data[k]
            elif v == "optional":
                continue
            elif k == "name":
                module_blk["module"][self.key][k] = self.name
            elif self.parent_layer is not None and k in self.parent_layer.outputs():
                module_blk["module"][self.key][
                    k
                ] = f"${{{{data.terraform_remote_state.parent.outputs.{k} }}}}"
            else:
                raise Exception(f"Unable to hydrate {k}")

        if "outputs" in self.desc:
            for k, v in self.desc["outputs"].items():
                if "export" in v and v["export"]:
                    if "output" not in module_blk:
                        module_blk["output"] = {}

                    module_blk["output"].update(
                        {k: {"value": f"${{{{module.{self.key}.{k} }}}}"}}
                    )

        return module_blk


class Module(BaseModule):
    pass
