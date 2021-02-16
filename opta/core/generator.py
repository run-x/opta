import logging
import os
from typing import Generator, List, Optional, Tuple

import yaml

from opta import gen_tf
from opta.constants import TF_FILE_PATH
from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.utils import deep_merge


def gen_all(configfile: str, env: Optional[str], var: List[str] = []) -> None:
    for _ in gen(configfile, env, var):
        pass


def gen(
    configfile: str, env: Optional[str], var: List[str] = []
) -> Generator[Tuple[int, int], None, None]:
    """ Generate TF file based on opta config file """
    if not os.path.exists(configfile):
        raise UserErrors(f"File {configfile} not found")

    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    for v in var:
        key, value = v.split("=")
        conf["meta"]["variables"] = conf["meta"].get("variables", {})
        conf["meta"]["variables"][key] = value

    layer = Layer.load_from_dict(conf, env)
    logging.debug("Loading infra blocks")

    total = len(layer.blocks)
    for block_idx, block in enumerate(layer.blocks):
        logging.debug(f"Generating block {block_idx}")
        ret = layer.gen_providers(block_idx, block.backend_enabled)
        ret = deep_merge(layer.gen_tf(block_idx), ret)

        gen_tf.gen(ret, TF_FILE_PATH)

        yield (block_idx, total)
