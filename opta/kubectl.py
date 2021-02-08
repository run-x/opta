import json
from typing import List, Optional, Tuple

import yaml

from opta.exceptions import UserErrors
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import fmt_msg, is_tool

KUBECTL_INSTALL_URL = (
    "https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html"
)
AWS_CLI_INSTALL_URL = (
    "https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
)
EKS_CLUSTER_NAME = "main"


def setup_kubectl(configfile: str, env: Optional[str]) -> None:
    """ Configure kubeconfig file with cluster details """
    # Make sure the user has the prerequisite CLI tools installed

    # kubectl may not *technically* be required for this opta command to run, but require
    # it anyways since user must install it to access the cluster.
    if not is_tool("kubectl"):
        raise UserErrors(
            f"Please visit this link to install kubectl first: {KUBECTL_INSTALL_URL}"
        )

    if not is_tool("aws"):
        raise UserErrors(
            f"Please visit the link to install the AWS CLI first: {AWS_CLI_INSTALL_URL}"
        )

    # Get the current account details from the AWS CLI.
    try:
        out = nice_run(
            ["aws", "sts", "get-caller-identity"], check=True, capture_output=True
        ).stdout.decode("utf-8")
    except Exception as err:
        raise UserErrors(
            fmt_msg(
                f"""Running the AWS CLI failed.
            Please make sure you've properly configured your AWS credentials,
            and recently refreshed them if they're expired:
            ~{err}"""
            )
        )

    aws_caller_identity = json.loads(out)
    current_aws_account_id = aws_caller_identity["Account"]

    # Get the environment's account details from the opta config
    env_aws_region, env_aws_account_ids = _get_cluster_env(configfile, env)

    # Make sure the current account points to the cluster environment
    if int(current_aws_account_id) not in env_aws_account_ids:
        raise UserErrors(
            fmt_msg(
                f"""The AWS CLI is not configured with
            the right credentials to access the {env or ""} cluster.
            ~Current AWS Account ID: {current_aws_account_id}
            ~Valid AWS Account IDs: {env_aws_account_ids}"""
            )
        )

    # Update kubeconfig with the cluster details, and also switches context
    nice_run(
        [
            "aws",
            "eks",
            "update-kubeconfig",
            "--name",
            EKS_CLUSTER_NAME,
            "--region",
            env_aws_region,
        ]
    )


def _get_cluster_env(configfile: str, env: Optional[str]) -> Tuple[str, List[int]]:
    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    layer = Layer.load_from_dict(conf, env)

    # Get the root environment layer
    while layer.parent is not None:
        layer = layer.parent

    aws_provider = layer.meta["providers"]["aws"]
    return aws_provider["region"], aws_provider["allowed_account_ids"]
