import os
import time

from ruamel.yaml import YAML

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util

init_template_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "init_templates"
)
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

REGISTRY = yaml.load(open(registry_path))
DEBUG_TREE = yaml.load(open(debugger_path))
VERSION = open(version_path).read().strip()
DEV_VERSION = "dev"

SESSION_ID = int(time.time() * 1000)

# Path of the generated tf file.
OPTA_DISABLE_REPORTING = "OPTA_DISABLE_REPORTING"
TF_FILE_PATH = "main.tf.json"
TF_PLAN_PATH = "tf.plan"
MAX_TERRAFORM_VERSION = "1.1.0"
MIN_TERRAFORM_VERSION = "0.15.0"
