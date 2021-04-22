from typing import TYPE_CHECKING, Optional

from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class ModuleProcessor:
    def __init__(self, module: "Module", layer: "Layer") -> None:
        self.layer = layer
        self.module = module

    def process(self, module_idx: int) -> None:
        if self.module.data.get("root_only", False) and self.layer.parent is not None:
            raise UserErrors(
                f"Module {self.module.name} can only specified in a root layer"
            )
        self.module.data["env_name"] = self.layer.get_env()
        self.module.data["layer_name"] = self.layer.name
        self.module.data["module_name"] = self.module.name

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        pass


class AWSK8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AWSK8sModuleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        from_parent = False
        eks_modules = self.layer.get_module_by_type("aws-eks", module_idx)
        if len(eks_modules) == 0 and self.layer.parent is not None:
            from_parent = True
            eks_modules = self.layer.parent.get_module_by_type("aws-eks")

        if len(eks_modules) == 0:
            raise UserErrors(
                "Did not find the aws-eks module in the layer or the parent layer"
            )
        eks_module = eks_modules[0]
        module_source = (
            "data.terraform_remote_state.parent.outputs"
            if from_parent
            else f"module.{eks_module.name}"
        )
        self.module.data[
            "openid_provider_url"
        ] = f"${{{{{module_source}.k8s_openid_provider_url}}}}"
        self.module.data[
            "openid_provider_arn"
        ] = f"${{{{{module_source}.k8s_openid_provider_arn}}}}"
        super(AWSK8sModuleProcessor, self).process(module_idx)


class GcpK8sModuleProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(GcpK8sModuleProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        super(GcpK8sModuleProcessor, self).process(module_idx)
