import json
import os
from typing import List, Optional, Tuple

import yaml

from opta import gen_tf  # noqa: E402
from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.output import get_terraform_outputs
from opta.utils import deep_merge, fmt_msg, is_tool

KUBECTL_INSTALL_URL = (
    "https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html"
)
AWS_CLI_INSTALL_URL = (
    "https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
)
DEFAULT_EKS_CLUSTER_NAME = "main"


def setup_kubectl(configfile: str, env: Optional[str]) -> None:
    """ Configure kubeconfig file with cluster details """
    # Make sure the user has the prerequisite CLI tools installed

    # kubectl may not *technically* be required for this opta command to run, but require
    # it anyways since user must install it to access the cluster.
    if not is_tool("kubectl"):
        raise Exception(
            f"Please visit this link to install kubectl first: {KUBECTL_INSTALL_URL}"
        )

    if not is_tool("aws"):
        raise Exception(
            f"Please visit the link to install the AWS CLI first: {AWS_CLI_INSTALL_URL}"
        )

    # Get the current account details from the AWS CLI.
    try:
        out = nice_run(
            ["aws", "sts", "get-caller-identity"], check=True, capture_output=True
        ).stdout.decode("utf-8")
    except Exception as err:
        raise Exception(
            fmt_msg(
                f"""
                Running the AWS CLI failed. Please make sure you've properly
                configured your AWS credentials, and recently refreshed them if
                they're expired:
                ~{err}
                """
            )
        )

    aws_caller_identity = json.loads(out)
    current_aws_account_id = aws_caller_identity["Account"]

    # Get the environment's account details from the opta config
    root_layer = _get_root_layer(configfile, env)
    env_aws_region, env_aws_account_ids = _get_cluster_env(root_layer)

    # Make sure the current account points to the cluster environment
    if int(current_aws_account_id) not in env_aws_account_ids:
        raise Exception(
            fmt_msg(
                f"""
                The AWS CLI is not configured with the right credentials to
                access the {env or ""} cluster.
                ~Current AWS Account ID: {current_aws_account_id}
                ~Valid AWS Account IDs: {env_aws_account_ids}
                """
            )
        )

    cluster_name = _get_eks_cluster_name(root_layer)
    # Update kubeconfig with the cluster details, and also switches context
    nice_run(
        [
            "aws",
            "eks",
            "update-kubeconfig",
            "--name",
            cluster_name,
            "--region",
            env_aws_region,
        ]
    )


def _get_cluster_env(root_layer: Layer) -> Tuple[str, List[int]]:
    aws_provider = root_layer.meta["providers"]["aws"]
    return aws_provider["region"], aws_provider["allowed_account_ids"]


def _get_eks_cluster_name(root_layer: Layer) -> str:
    # Find the block that contains the aws-eks-init module, which has the
    # cluster name as an output
    eks_module_block = None
    eks_module_block_idx = None
    for block_idx, block in enumerate(root_layer.blocks):
        for module in block.modules:
            if module.key == "aws-eks-init":
                eks_module_block = block
                eks_module_block_idx = block_idx
                break

    if eks_module_block is None:
        print(
            f'Cannot find EKS cluster name, defaulting to "{DEFAULT_EKS_CLUSTER_NAME}"...'
        )
        return DEFAULT_EKS_CLUSTER_NAME

    # Generate the terraform file so outputs can be fetched.
    ret = root_layer.gen_providers(eks_module_block_idx, block.backend_enabled)  # type: ignore
    ret = deep_merge(root_layer.gen_tf(eks_module_block_idx), ret)  # type: ignore

    tmp_tf_file = "tmp.tf.json"
    gen_tf.gen(ret, tmp_tf_file)

    # Get the cluster name from the outputs.
    outputs_raw = get_terraform_outputs(True)
    outputs = json.loads(outputs_raw)
    # Use unsafe key accessing so fails loudly if the cluster name is not exported.
    cluster_name = outputs["k8s_cluster_name"]["value"]

    os.remove(tmp_tf_file)
    return cluster_name


def _get_root_layer(configfile: str, env: Optional[str]) -> Layer:
    conf = yaml.load(open(configfile), Loader=yaml.Loader)
    layer = Layer.load_from_dict(conf, env)

    while layer.parent is not None:
        layer = layer.parent

    return layer
