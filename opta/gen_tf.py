import json
from typing import Any, Mapping


def gen(blocks: Mapping[Any, Any], out_file: str) -> None:
    with open(out_file, "w") as f:
        f.write(json.dumps(blocks, indent=2))

    print(f"Output written to {out_file}")
