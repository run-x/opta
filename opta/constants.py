import os
import time
from typing import Dict

from ruamel.yaml import YAML

from opta.registry import make_registry_dict

yaml = YAML(
    typ="safe"
)  # Duplicate because constants can't import utils and yaml really is a util

init_template_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "init_templates"
)
version_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "version.txt"
)
tf_modules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")

one_time_run = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".first_time_run")

REGISTRY = make_registry_dict()
VERSION = open(version_path).read().strip()
DEV_VERSION = "dev"

SESSION_ID = int(time.time() * 1000)
UPGRADE_WARNINGS: Dict[str, str] = {
    "0.21.0": "Performing updates on AWS environments to the network load balancer which will cause a new one to be "
    "spawned (old one will stick around, but should be manually deleted). Opta-internal references, like "
    "those for the opts managed dns, will be switched to new load balancer automatically, but this may cuase "
    "a 5 minute downtime as the new load balancer becomes operational."
}

# Path of the generated tf file.
OPTA_DISABLE_REPORTING = "OPTA_DISABLE_REPORTING"
TF_FILE_PATH = "main.tf.json"
TF_PLAN_PATH = "tf.plan"
MAX_TERRAFORM_VERSION = "1.1.0"
MIN_TERRAFORM_VERSION = "0.15.0"

CI = "CI"

# List of chars to escape in regexes
ESCAPE_REQUIRED = ["\\", ".", "+", "*", "?", "[", "]", "$", "^", "(", ")", "{", "}", "|"]

SHELLS_ALLOWED = ["bash", "sh"]

"""
Note: Key in Module Dependency should have all the dependencies present in the set.
"""
MODULE_DEPENDENCY = {
    "aws-k8s-base": {"aws-eks"},
    "azure-kys-base": {"azure-aks"},
    "gcp-k8s-base": {"gcp-gke"},
}
