import os
import shutil

from opta.constants import TF_FILE_PATH, TF_PLAN_PATH

TF_DIR = ".terraform"
TF_LOCK = ".terraform.lock.hcl"
TF_STATE_FILE = "terraform.tfstate"
TF_STATE_BACKUP_FILE = "terraform.tfstate.backup"


def cleanup_files() -> None:
    for f in [TF_FILE_PATH, TF_LOCK, TF_PLAN_PATH, TF_STATE_FILE, TF_STATE_BACKUP_FILE]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    if os.path.isdir(TF_DIR):
        shutil.rmtree(TF_DIR)

    for f in os.listdir("."):
        if os.path.isfile(f) and f.startswith("tmp.opta."):
            os.remove(f)
