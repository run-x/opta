from typing import TYPE_CHECKING, List

from opta.module_processors.base import ModuleProcessor

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class K8sServiceProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if module.data["type"] != "k8s-service":
            raise Exception(
                f"The module {module.key} was expected to be of type k8s service"
            )
        self.read_buckets: list[str] = []
        self.write_buckets: list[str] = []
        super(K8sServiceProcessor, self).__init__(module, layer)

    def process(self, block_idx: int) -> None:
        current_modules = []
        for block in self.layer.blocks[0 : block_idx + 1]:
            current_modules += block.modules

        # Update the secrets
        transformed_secrets = []
        if "original_secrets" in self.module.data:
            secrets = self.module.data["original_secrets"]
        else:
            secrets = self.module.data.get("secrets", [])
            self.module.data["original_secrets"] = secrets
        for secret in secrets:
            if type(secret) is str:
                transformed_secrets.append({"name": secret, "value": ""})
            else:
                raise Exception("Secret must be string or dict")
        self.module.data["secrets"] = transformed_secrets

        # Handle links
        for target_module_name, link_permissions in self.module.data.get(
            "links", {}
        ).items():
            module = self.layer.get_module(target_module_name, block_idx)
            if module is None:
                raise Exception(f"Did not find the desired module {target_module_name}")
            module_type = module.data["type"]
            if module_type == "aws-rds":
                self.handle_rds_link(module, link_permissions)
            elif module_type == "aws-redis":
                self.handle_redis_link(module, link_permissions)
            elif module_type == "aws-documentdb":
                self.handle_docdb_link(module, link_permissions)
            elif module_type == "aws-s3-bucket":
                self.handle_s3_link(module, link_permissions)
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
        if self.read_buckets:
            iam_statements.append(
                {
                    "Sid": "ReadBuckets",
                    "Action": [
                        "s3:GetObject*",
                        "s3:ListBucket",
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}" for bucket_name in self.read_buckets
                    ]
                    + [
                        f"arn:aws:s3:::{bucket_name}/*"
                        for bucket_name in self.read_buckets
                    ],
                }
            )
        if self.write_buckets:
            iam_statements.append(
                {
                    "Sid": "WriteBuckets",
                    "Action": [
                        "s3:GetObject*",
                        "s3:PutObject*",
                        "s3:DeleteObject*",
                        "s3:ListBucket",
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}"
                        for bucket_name in self.write_buckets
                    ]
                    + [
                        f"arn:aws:s3:::{bucket_name}/*"
                        for bucket_name in self.write_buckets
                    ],
                }
            )
        self.module.data["iam_policy"] = {
            "Version": "2012-10-17",
            "Statement": iam_statements,
        }

    def handle_rds_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        for key in ["db_user", "db_name", "db_password", "db_host"]:
            self.module.data["secrets"].append(
                {
                    "name": f"{linked_module.key}_{key}",
                    "value": f"${{{{module.{linked_module.key}.{key}}}}}",
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
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        for key in ["cache_host", "cache_auth_token"]:
            self.module.data["secrets"].append(
                {
                    "name": f"{linked_module.key}_{key}",
                    "value": f"${{{{module.{linked_module.key}.{key}}}}}",
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
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        for key in ["db_user", "db_host", "db_password"]:
            self.module.data["secrets"].append(
                {
                    "name": f"{linked_module.key}_{key}",
                    "value": f"${{{{module.{linked_module.key}.{key}}}}}",
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

    def handle_s3_link(
        self, linked_module: "Module", link_permissions: List[str]
    ) -> None:
        bucket_name = linked_module.data["bucket_name"]
        for permission in link_permissions:
            if permission == "read":
                self.read_buckets.append(bucket_name)
            elif permission == "write":
                self.write_buckets.append(bucket_name)
            else:
                raise Exception(f"Invalid permission {permission}")
