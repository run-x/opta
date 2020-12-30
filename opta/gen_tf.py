from typing import Any, Iterable, Mapping


def gen(blocks: Iterable[Mapping[Any, Any]], out_file: str) -> None:
    print(blocks)
    print(f"Output written to {out_file}")
