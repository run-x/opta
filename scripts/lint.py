#!/usr/bin/env python

import argparse
import logging
import os
import subprocess
import sys
from typing import Collection, List

# One script for all linting
# By default runs all checks on the whole repo (used via CI)
# With --precommit runs checks on staged files
# Fixes what can be fixed and does git add
# [TODO] With --prettier runs prettier on modified files
# [TODO] With --py runs python checks on the whole repo
# [TODO] With --js runs js checks on the whole repo


def main(precommit: bool, apply: bool) -> None:
    files_changed = []
    if precommit:
        diff_cmd = ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"]
        files_changed = subprocess.check_output(diff_cmd).decode("utf-8").split()
        logging.info(f"Changed files: {files_changed}")

    ret = 0

    ret = py_check(files_changed, precommit, apply) or ret

    if ret >= 256:
        ret = 1
    elif precommit:
        # Add to git
        ret = os.system(f"git add {' '.join(files_changed)}") or ret

    sys.exit(ret)


def py_check(files_changed: Collection[str], precommit: bool, apply: bool) -> int:
    if not precommit:
        files_changed = ["."]
    else:
        files_changed = list(filter(lambda x: x.endswith(".py"), files_changed))
        if len(files_changed) == 0:
            return 0

    isort = "pipenv run isort --check-only"
    black = "pipenv run black --check"
    flake8 = "pipenv run flake8 --exclude examples"
    mypy = "pipenv run mypy --exclude examples"

    if precommit or apply:
        isort = "pipenv run isort"
        black = "pipenv run black"
        flake8 = "pipenv run flake8 --exclude examples"
        mypy = "pipenv run mypy --exclude examples"

    linters = [
        f"{linter} {' '.join(files_changed)}" for linter in [isort, black, flake8, mypy]
    ]

    logging.info("Running JSON schema check...")

    logging.info("Running py checks...")
    return execute_commands(linters)


def execute_commands(commands: List[str]) -> int:
    if len(commands) == 0:
        return 0
    cmd = commands[0]
    logging.info(cmd)
    result = os.system(cmd)
    logging.info("Success" if result == 0 else f"Error when running: {cmd}")
    return result if result > 0 else execute_commands(commands[1:])


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
    parser.add_argument(
        "--apply", action="store_true", help="Apply fixes if possible", default=False
    )
    args = parser.parse_args()

    main(args.precommit, args.apply)
