from typing import TYPE_CHECKING, Dict, List, Optional, Union

from modules.base import AWSIamAssembler, AWSK8sModuleProcessor, K8sServiceModuleProcessor
from modules.linker_helper import LinkerHelper
from opta.core.kubernetes import create_namespace_if_not_exists, list_namespaces
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsK8sServiceProcessor(
    AWSK8sModuleProcessor, K8sServiceModuleProcessor, AWSIamAssembler
):
    FLAG_MULTIPLE_PORTS_SUPPORTED = True

    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-k8s-service":
            raise Exception(
                f"The module {module.name} was expected to be of type aws k8s service"
            )
        super(AwsK8sServiceProcessor, self).__init__(module, layer)

    def pre_hook(self, module_idx: int) -> None:
        list_namespaces()
        create_namespace_if_not_exists(self.layer.name)
        super(AwsK8sServiceProcessor, self).pre_hook(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        self._extra_ports_controller()

        super().post_hook(module_idx, exception)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["link_secrets"] = self.module.data.get("link_secrets", [])

        current_envars: Union[List, Dict[str, str]] = self.module.data.get("env_vars", [])
        if isinstance(current_envars, dict):
            self.module.data["env_vars"] = [
                {"name": x, "value": y} for x, y in current_envars.items()
            ]

        # Handle links
        for link_data in self.module.data.get("links", []):
            if type(link_data) is str:
                target_module_name = link_data
                link_permissions = []
            elif type(link_data) is dict:
                target_module_name = list(link_data.keys())[0]
                link_permissions = list(link_data.values())[0]
            else:
                raise UserErrors(
                    f"Link data {link_data} must be a string or map holding the permissions"
                )
            module = self.layer.get_module(target_module_name, module_idx)
            if module is None:
                raise Exception(
                    f"Did not find the desired module {target_module_name} "
                    "make sure that the module you're referencing is listed before the k8s "
                    "app one"
                )
            module_type = module.aliased_type or module.type
            if module_type == "aws-postgres":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "aws-mysql":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_name", "db_password", "db_host"],
                )
            elif module_type == "aws-redis":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["cache_host", "cache_auth_token"],
                )
            elif module_type == "aws-documentdb":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=["db_user", "db_host", "db_password"],
                )
            elif module_type == "aws-s3":
                self.handle_s3_link(module, link_permissions)
            elif module_type == "aws-sqs":
                self.handle_sqs_link(module, link_permissions)
            elif module_type == "aws-sns":
                self.handle_sns_link(module, link_permissions)
            elif module_type == "aws-dynamodb":
                self.handle_dynamodb_link(module, link_permissions)
            elif module_type == "mongodb-atlas":
                LinkerHelper.handle_link(
                    module=self.module,
                    linked_module=module,
                    link_permissions=link_permissions,
                    required_vars=[
                        "db_password",
                        "db_user",
                        "mongodb_atlas_connection_string",
                    ],
                )
            else:
                raise Exception(
                    f"Unsupported module type for k8s service link: {module_type}"
                )
        iam_statements = [
            {
                "Sid": "DescribeCluster",
                "Action": ["eks:DescribeCluster"],
                "Effect": "Allow",
                "Resource": ["*"],
            }
        ]
        iam_statements += self.prepare_iam_statements()
        self.module.data["iam_policy"] = {
            "Version": "2012-10-17",
            "Statement": iam_statements,
        }
        if "image_tag" in self.layer.variables:
            self.module.data["tag"] = self.layer.variables["image_tag"]

        if "image_digest" in self.layer.variables:
            self.module.data["digest"] = self.layer.variables["image_digest"]
        seen = set()
        self.module.data["link_secrets"] = [
            seen.add(obj["name"]) or obj  # type: ignore
            for obj in self.module.data["link_secrets"]
            if obj["name"] not in seen
        ]
        super(AwsK8sServiceProcessor, self).process(module_idx)
