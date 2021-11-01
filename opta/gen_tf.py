from typing import Any, Mapping

from opta.utils import json, logger


def gen(tf_blocks: Mapping[Any, Any], out_file: str) -> None:
    with open(out_file, "w") as f:
        f.write(json.dumps(tf_blocks, indent=2))

    logger.debug(f"Output written to {out_file}")
