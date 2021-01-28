#!/usr/bin/env python

import argparse
import logging
import os
import subprocess
import sys
from typing import Collection

# One script for all linting
# By default runs all checks on the whole repo (used via CI)
# With --precommit runs checks on staged files
# Fixes what can be fixed and does git add
# [TODO] With --prettier runs prettier on modified files
# [TODO] With --py runs python checks on the whole repo
# [TODO] With --js runs js checks on the whole repo


def main(precommit: bool) -> None:
    files_changed = []
    if precommit:
        diff_cmd = ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"]
        files_changed = subprocess.check_output(diff_cmd).decode("utf-8").split()
        logging.info(f"Changed files: {files_changed}")

    ret = 0

    ret = py_check(files_changed, precommit) or ret

    if ret >= 256:
        ret = 1
    elif precommit:
        # Add to git
        ret = os.system(f"git add {' '.join(files_changed)}") or ret

    sys.exit(ret)


def py_check(files_changed: Collection[str], precommit: bool) -> int:
    if not precommit:
        files_changed = ["."]
    else:
        files_changed = list(filter(lambda x: x.endswith(".py"), files_changed))
        if len(files_changed) == 0:
            return 0

    isort = "pipenv run isort --check-only"
    black = "echo ''"  # no-op
    flake8 = "pipenv run flake8"

    mypy = "pipenv run mypy"

    if precommit:
        isort = "pipenv run isort"
        black = "pipenv run black"
        flake8 = "pipenv run flake8"
        mypy = "pipenv run mypy"

    cmd = f"{isort} {' '.join(files_changed)}\
        && {black} {' '.join(files_changed)}\
        && {flake8} {' '.join(files_changed)}\
        && {mypy} {' '.join(files_changed)}"

    logging.info("Running py checks...")
    logging.info(cmd)

    return os.system(cmd)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser("lint")
    parser.add_argument(
        "--precommit", action="store_true", help="Run in precommit mode", default=False
    )
    args = parser.parse_args()

    main(args.precommit)
