import os

from dotenv import dotenv_values

from opta.core.kubernetes import get_namespaced_secrets, update_secrets
from opta.exceptions import UserErrors
from opta.utils import deep_merge, logger

MANUAL_SECRET_NAME = "manual-secrets"  # nosec
LINKED_SECRET_NAME = "secret"  # nosec


def get_secrets(namespace: str, manual_secret_name: str) -> dict:
    """:return: manual and linked secrets"""
    manual_secrets = get_namespaced_secrets(namespace, manual_secret_name)
    linked_secrets = get_namespaced_secrets(
        namespace, LINKED_SECRET_NAME
    )  # Helm charts don't have linked secrets, but it'll just return an empty dict so no worries
    for secret_name in manual_secrets.keys():
        if secret_name in linked_secrets:
            logger.warning(
                f"# Secret {secret_name} found manually overwritten from linked value."
            )
            del linked_secrets[secret_name]
    return deep_merge(manual_secrets, linked_secrets)


def bulk_update_manual_secrets(
    namespace: str, manual_secret_name: str, env_file: str
) -> None:
    """
    append the values from the env file to the existing data for this manual secret.

    create the secret if it doesn't exist yet.

    :raises UserErrors: if env_file is not found
    """
    if not os.path.exists(env_file):
        raise UserErrors(f"Could not find file {env_file}")
    new_values = dotenv_values(env_file)
    update_secrets(namespace, manual_secret_name, new_values)
