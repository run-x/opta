from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from opta.core.kubernetes import (
    create_namespace_if_not_exists,
    get_manual_secrets,
    list_namespaces,
)
from opta.exceptions import UserErrors
from opta.module_processors.base import (
    AWSIamAssembler,
    AWSK8sModuleProcessor,
    K8sServiceModuleProcessor,
)
from opta.module_processors.linker_helper import LinkerHelper

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
        manual_secrets = get_manual_secrets(self.layer.name)
        for secret_name in self.module.data.get("secrets", []):
            if secret_name not in manual_secrets:
                raise UserErrors(
                    f"Secret {secret_name} has not been set via opta secret update! Please do so before applying the "
                    f"K8s service w/ a new secret."
                )
        super(AwsK8sServiceProcessor, self).pre_hook(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        self._extra_ports_controller()

        super().post_hook(module_idx, exception)

    def process(self, module_idx: int) -> None:
        # Update the secrets
        self.module.data["manual_secrets"] = self.module.data.get("secrets", [])
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
                self.handle_rds_link(module, link_permissions)
            elif module_type == "aws-redis":
                self.handle_redis_link(module, link_permissions)
            elif module_type == "aws-documentdb":
                self.handle_docdb_link(module, link_permissions)
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

    # TODO: consolidated repeated credential link code
    def handle_rds_link(
        self, linked_module: "Module", link_permissions: List[Any]
    ) -> None:
        required_db_vars = ["db_user", "db_name", "db_password", "db_host"]
        renamed_vars = {}
        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_db_vars
            ):
                raise UserErrors(
                    f"To rename db variables you must provide aliases for these fields: {required_db_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("DB variable rename must be only to another string")

        for key in required_db_vars:
            self.module.data["link_secrets"].append(
                {
                    "name": renamed_vars.get(key, f"{linked_module.name}_{key}"),
                    "value": f"${{{{module.{linked_module.name}.{key}}}}}",
                }
            )
        if link_permissions:
            raise Exception(
                "We're not supporting IAM permissions for rds right now. "
                "Your k8s service will have the db user, name, password, "
                "and host as envars (pls see docs) and these IAM "
                "permissions are for manipulating the db itself, which "
                "I don't think is what you're looking for."
            )

    def handle_redis_link(
        self, linked_module: "Module", link_permissions: List[Any]
    ) -> None:
        required_redis_vars = ["cache_host", "cache_auth_token"]
        renamed_vars = {}

        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_redis_vars
            ):
                raise UserErrors(
                    f"To rename redis variables you must provide aliases for these fields: {required_redis_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("Redis variable rename must be only to another string")

        for key in required_redis_vars:
            self.module.data["link_secrets"].append(
                {
                    "name": renamed_vars.get(key, f"{linked_module.name}_{key}"),
                    "value": f"${{{{module.{linked_module.name}.{key}}}}}",
                }
            )
        if link_permissions:
            raise Exception(
                "We're not supporting IAM permissions for redis right now. "
                "Your k8s service will have the cache's host and auth token "
                "as envars (pls see docs) and these IAM permissions "
                "are for manipulating the redis cluster itself, which "
                "I don't think is what you're looking for."
            )

    def handle_docdb_link(
        self, linked_module: "Module", link_permissions: List[Any]
    ) -> None:
        required_docdb_vars = ["db_user", "db_host", "db_password"]
        renamed_vars = {}

        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_docdb_vars
            ):
                raise UserErrors(
                    f"To rename docdb variables you must provide aliases for these fields: {required_docdb_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("Docdb variable rename must be only to another string")

        for key in required_docdb_vars:
            self.module.data["link_secrets"].append(
                {
                    "name": renamed_vars.get(key, f"{linked_module.name}_{key}"),
                    "value": f"${{{{module.{linked_module.name}.{key}}}}}",
                }
            )
        if link_permissions:
            raise Exception(
                "We're not supporting IAM permissions for docdb right now. "
                "Your k8s service will have the db's user, password and "
                "host as envars (pls see docs) and these IAM permissions "
                "are for manipulating the docdb cluster itself, which "
                "I don't think is what you're looking for."
            )
