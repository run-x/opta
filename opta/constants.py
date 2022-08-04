import os
import time
from os.path import expanduser
from typing import Dict, Final, Optional, Tuple

from kubernetes.config.kube_config import KUBE_CONFIG_DEFAULT_LOCATION

from opta.registry import make_registry_dict

init_template_path: Final = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "init_templates"
)
version_path: Final = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "version.txt"
)
tf_modules_path: Final = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "modules"
)

one_time_run: Final = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".first_time_run"
)

REGISTRY: Final = make_registry_dict()
with open(version_path) as f:
    VERSION: Final = f.read().strip()
DEV_VERSION: Final = "dev"

SESSION_ID: Final = int(time.time() * 1000)

# This dictionary is to be used to give warnings to users about potential outages/breaking changes
# caused by opta version upgrade. The key is the first version that the warning is for. So if you have a
# warning for versions 0.1.0, 0.2.0, 0.4.0, and 0.5.0, and the user used to have version 0.2.0, but now has version
# 0.5.0, then they will see warnings for 0.4.0, and 0.5.0
UPGRADE_WARNINGS: Final[Dict[Tuple[str, str, str], str]] = {
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
OPTA_DISABLE_REPORTING: Final = "OPTA_DISABLE_REPORTING"
TF_FILE_PATH: Final = "main.tf.json"
TF_PLAN_PATH: Final = "tf.plan"
MAX_TERRAFORM_VERSION: Final = "2.0.0"
MIN_TERRAFORM_VERSION: Final = "0.15.0"

CI: Final = "CI"

SHELLS_ALLOWED: Final = ("bash", "sh")

REDS: Final = (1, 9, 124, 160, 196)

OPTA_INSTALL_URL: Final = "https://docs.opta.dev/install.sh"
successfull_upgrade: Final = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".successfull_upgrade"
)

HOME: Final = expanduser("~")
DEFAULT_KUBECONFIG = expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
GENERATED_KUBE_CONFIG_DIR: Final = f"{HOME}/.opta/kubeconfigs"
GENERATED_KUBE_CONFIG: Optional[str] = None
ONE_WEEK_UNIX: Final = 604800
