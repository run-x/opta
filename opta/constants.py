import os
import time

import yaml

schema_dir_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "schema"
)
registry_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "registry.yaml"
)
debugger_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "debugger.yaml"
)
version_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "version.txt"
)
tf_modules_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "tf_modules"
)

REGISTRY = yaml.load(open(registry_path), Loader=yaml.SafeLoader)
DEBUG_TREE = yaml.load(open(debugger_path), Loader=yaml.SafeLoader)
VERSION = open(version_path).read().strip()
DEV_VERSION = "dev"

SESSION_ID = int(time.time() * 1000)

# Path of the generated tf file.
OPTA_DISABLE_REPORTING = "OPTA_DISABLE_REPORTING"
TF_FILE_PATH = "main.tf.json"
TF_PLAN_PATH = "tf.plan"
MAX_TERRAFORM_VERSION = "0.16.0"
MIN_TERRAFORM_VERSION = "0.15.0"
