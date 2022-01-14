import os

from dotenv import dotenv_values

from opta.core.kubernetes import get_namespaced_secrets, update_secrets
from opta.exceptions import UserErrors
from opta.utils import deep_merge

MANUAL_SECRET_NAME = "manual-secrets"  # nosec
LINKED_SECRET_NAME = "secret"  # nosec


def get_secrets(layer_name: str) -> dict:
    """:return: manual and linked secrets"""
    return deep_merge(get_manual_secrets(layer_name), get_linked_secrets(layer_name))


def get_manual_secrets(layer_name: str) -> dict:
    """:return: manual secrets, saved in the secret called 'manual-secrets'"""
    return get_namespaced_secrets(layer_name, MANUAL_SECRET_NAME)


def get_linked_secrets(layer_name: str) -> dict:
    """:return: manual secrets, saved in the secret called 'secret'"""
    return get_namespaced_secrets(layer_name, LINKED_SECRET_NAME)


def update_manual_secrets(layer_name: str, new_values: dict) -> None:
    """
    append the new values to the existing data for this manual secret.

    create the secret if it doesn't exist yet.
    """
    update_secrets(layer_name, MANUAL_SECRET_NAME, new_values)


def bulk_update_manual_secrets(layer_name: str, env_file: str) -> None:
    """
    append the values from the env file to the existing data for this manual secret.

    create the secret if it doesn't exist yet.

    :raises UserErrors: if env_file is not found
    """
    if not os.path.exists(env_file):
        raise UserErrors(f"Could not find file {env_file}")
    new_values = dotenv_values(env_file)
    update_manual_secrets(layer_name, new_values)
