import logging
import os
from typing import List, Optional, Set

import yaml

from opta import gen_tf
from opta.constants import TF_FILE_PATH
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import deep_merge


def gen(
    configfile: str,
    env: Optional[str],
    var: List[str] = [],
    max_block: Optional[int] = None,
) -> None:
    """ Generate TF file based on opta config file """
    if not os.path.exists(configfile):
        raise UserErrors(f"File {configfile} not found")

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    for v in var:
        key, value = v.split("=")
        conf["meta"]["variables"] = conf["meta"].get("variables", {})
        conf["meta"]["variables"][key] = value

    layer = Layer.load_from_dict(conf, env)
    current_module_keys: Set[str] = set()
    total_modules_applied: Set[str] = set()
    logging.debug("Loading infra blocks")
    blocks_to_process = (
        layer.blocks[: max_block + 1] if max_block is not None else layer.blocks
    )
    for block_idx, block in enumerate(blocks_to_process):
        current_module_keys = current_module_keys.union(
            set(map(lambda x: x.key, block.modules))
        )

        # TODO someone needs to fetch s3 state

        if current_module_keys.issubset(total_modules_applied) and block_idx + 1 != len(
            blocks_to_process
        ):
            continue
        logging.debug(
            f"Generating block {block_idx} for modules {current_module_keys}..."
        )
        ret = layer.gen_providers(block_idx, block.backend_enabled)
        ret = deep_merge(layer.gen_tf(block_idx), ret)

        gen_tf.gen(ret, TF_FILE_PATH)
        logging.debug(
            f"Will now initialize generate terraform plan for block {block_idx}."
        )

        block_idx += 1
