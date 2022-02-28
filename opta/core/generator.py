from typing import TYPE_CHECKING, Generator, List, Optional, Tuple

import click
from colored import attr

from opta import gen_tf
from opta.constants import TF_FILE_PATH
from opta.core.kubernetes import cluster_exist, current_image_digest_tag, set_kube_config
from opta.utils import deep_merge, logger

if TYPE_CHECKING:
    from opta.layer import Layer, StructuredConfig
    from opta.module import Module


def gen_all(layer: "Layer", existing_config: Optional["StructuredConfig"] = None) -> None:
    # Just run the generator till the end
    list(gen(layer, existing_config))


def gen(
    layer: "Layer",
    existing_config: Optional["StructuredConfig"] = None,
    image_tag: Optional[str] = None,
    image_digest: Optional[str] = None,
    test: bool = False,
    check_image: bool = False,
    auto_approve: bool = False,
) -> Generator[Tuple[int, List["Module"], int], None, None]:
    """Generate TF file based on opta config file"""
    logger.debug("Loading infra blocks")

    total_module_count = len(layer.modules)
    current_modules = []
    for module_idx, module in enumerate(layer.modules):
        logger.debug(f"Generating {module_idx} - {module.name}")
        current_modules.append(module)
        if not module.halt and module_idx + 1 != total_module_count:
            continue
        service_modules = layer.get_module_by_type("k8s-service", module_idx)
        if check_image and len(service_modules) > 0 and cluster_exist(layer.root()):
            set_kube_config(layer)

            for service_module in service_modules:
                current_image_info = current_image_digest_tag(layer)
                if (
                    image_digest is None
                    and (
                        current_image_info["tag"] is not None
                        or current_image_info["digest"] is not None
                    )
                    and image_tag is None
                    and service_module.data.get("image", "").upper() == "AUTO"
                    and not test
                ):
                    if not auto_approve:
                        if click.confirm(
                            f"WARNING There is an existing deployment (tag={current_image_info['tag']}, "
                            f"digest={current_image_info['digest']}) and the pods will be killed as you "
                            f"did not specify an image tag. Would you like to keep the existing deployment alive?",
                        ):
                            image_tag = current_image_info["tag"]
                            image_digest = current_image_info["digest"]
                    else:
                        logger.info(
                            f"{attr('bold')}Using the existing deployment {attr('underlined')}"
                            f"(tag={current_image_info['tag']}, digest={current_image_info['digest']}).{attr(0)}\n"
                            f"{attr('bold')}If you wish to deploy another image, please use "
                            f"{attr('bold')}{attr('underlined')} opta deploy command.{attr(0)}"
                        )
                        image_tag = current_image_info["tag"]
                        image_digest = current_image_info["digest"]
        layer.variables["image_tag"] = image_tag
        layer.variables["image_digest"] = image_digest
        ret = layer.gen_providers(module_idx)
        ret = deep_merge(layer.gen_tf(module_idx, existing_config), ret)

        gen_tf.gen(ret, TF_FILE_PATH)

        yield module_idx, current_modules, total_module_count


# Generate a tags override file in every module, that adds opta tags to every resource.
def gen_opta_resource_tags(layer: "Layer") -> None:
    if "aws" in layer.providers:
        for module in layer.modules:
            module.gen_tags_override()
