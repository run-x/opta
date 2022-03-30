import os
import time
from os.path import expanduser
from typing import Dict, Optional, Tuple

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

# This dictionary is to be used to give warnings to users about potential outages/breaking changes
# caused by opta version upgrade. The key is the first version that the warning is for. So if you have a
# warning for versions 0.1.0, 0.2.0, 0.4.0, and 0.5.0, and the user used to have version 0.2.0, but now has version
# 0.5.0, then they will see warnings for 0.4.0, and 0.5.0
UPGRADE_WARNINGS: Dict[Tuple[str, str, str], str] = {
    (
        "0.21.0",
        "aws",
        "aws-k8s-base",
    ): "If you are applying to an AWS environment, this upgrade will cause a 5 min downtime for "
    "any public traffic, as this will replace the network load balancer with a new, superior-managed one"
    "(old one will stick around, but should be manually deleted). Opta-internal references, like "
    "those for the opta managed dns, will be switched to new load balancer automatically, but this may cause "
    "a 5 minute downtime as the new load balancer becomes operational."
}

# Path of the generated tf file.
OPTA_DISABLE_REPORTING = "OPTA_DISABLE_REPORTING"
TF_FILE_PATH = "main.tf.json"
TF_PLAN_PATH = "tf.plan"
MAX_TERRAFORM_VERSION = "2.0.0"
MIN_TERRAFORM_VERSION = "0.15.0"

CI = "CI"

# List of chars to escape in regexes
ESCAPE_REQUIRED = ["\\", ".", "+", "*", "?", "[", "]", "$", "^", "(", ")", "{", "}", "|"]

SHELLS_ALLOWED = ["bash", "sh"]


REDS = [1, 9, 124, 160, 196]

OPTA_INSTALL_URL = "https://docs.opta.dev/install.sh"
successfull_upgrade = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".successfull_upgrade"
)

HOME = expanduser("~")
GENERATED_KUBE_CONFIG_DIR = f"{HOME}/.opta/kubeconfigs"
GENERATED_KUBE_CONFIG: Optional[str] = None
ONE_WEEK_UNIX = 604800
