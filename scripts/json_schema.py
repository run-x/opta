#!/usr/bin/env python
import argparse

from opta.json_schema import check_schemas

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--write",
        action="store_const",
        const=True,
        help="Allow script to overwrite file contents for autofixable errors",
    )
    args = parser.parse_args()
    check_schemas(write=args.write)
