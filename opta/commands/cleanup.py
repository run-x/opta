import os
import shutil

import click

TERRAFORM_DIR = ".terraform"
TERRAFORM_LOCK = ".terraform.lock.hcl"


@click.command(hidden=True)
def cleanup() -> None:
    """Additionally cleans up all generated terraform files"""
    if os.path.isdir(TERRAFORM_DIR):
        shutil.rmtree(TERRAFORM_DIR)

    if os.path.exists(TERRAFORM_LOCK):
        os.remove(TERRAFORM_LOCK)

    # Note that opta.cli._cleanup() cleans up a few other
    # opta generated files.
