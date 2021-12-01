from typing import Any, List

from opta.exceptions import UserErrors
from opta.module import Module


class LinkerHelper:
    @staticmethod
    def handle_link(
        module: "Module",
        linked_module: "Module",
        link_permissions: List[Any],
        required_vars: List[Any],
    ) -> None:

        renamed_vars = {}
        if len(link_permissions) > 0:
            renamed_vars = link_permissions.pop()
            if not isinstance(renamed_vars, dict) or set(renamed_vars.keys()) != set(
                required_vars
            ):
                raise UserErrors(
                    f"To rename db variables you must provide aliases for these fields: {required_vars}"
                )
            if not all(map(lambda x: isinstance(x, str), renamed_vars.values())):
                raise UserErrors("DB variable rename must be only to another string")

        for key in required_vars:
            module.data["link_secrets"].append(
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
