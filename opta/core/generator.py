from typing import TYPE_CHECKING, Generator, List, Tuple

from opta import gen_tf
from opta.constants import TF_FILE_PATH
from opta.utils import deep_merge, logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


def gen_all(layer: "Layer") -> None:
    # Just run the generator till the end
    list(gen(layer))


def gen(layer: "Layer") -> Generator[Tuple[int, List["Module"], int], None, None]:
    """ Generate TF file based on opta config file """
    logger.debug("Loading infra blocks")

    total_module_count = len(layer.modules)
    current_modules = []
    for module_idx, module in enumerate(layer.modules):
        logger.debug(f"Generating {module_idx}")
        current_modules.append(module)
        if not module.halt and module_idx + 1 != total_module_count:
            continue
        ret = layer.gen_providers(module_idx)
        ret = deep_merge(layer.gen_tf(module_idx), ret)

        gen_tf.gen(ret, TF_FILE_PATH)

        yield module_idx, current_modules, total_module_count


# Generate a tags override file in every module, that adds opta tags to every resource.
def gen_opta_resource_tags(layer: "Layer") -> None:
    if "aws" in layer.providers:
        for module in layer.modules:
            module.gen_tags_override()
