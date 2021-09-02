#!/usr/bin/env python
import argparse

from opta.registry import make_registry_docs

if __name__ == "__main__":
    parser = argparse.ArgumentParser("docs")
    parser.add_argument(
        "directory", type=str, help="Root directory to add the auto-generated docs in",
    )
    args = parser.parse_args()

    make_registry_docs(args.directory)
