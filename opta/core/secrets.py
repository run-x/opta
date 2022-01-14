

import os
from opta.core.kubernetes import get_namespaced_secrets, update_secrets
from opta.exceptions import UserErrors
from opta.utils import deep_merge
from dotenv import dotenv_values


MANUAL_SECRET_NAME = "manual-secrets"
LINKED_SECRET_NAME = "secret"


def get_secrets(layer_name: str) -> dict:
    return deep_merge(get_manual_secrets(layer_name), get_linked_secrets(layer_name))


def get_manual_secrets(layer_name: str) -> dict:
    return get_namespaced_secrets(layer_name, MANUAL_SECRET_NAME)


def get_linked_secrets(layer_name: str) -> dict:
    return get_namespaced_secrets(layer_name, LINKED_SECRET_NAME)


def update_manual_secrets(layer_name: str, new_values: dict) -> None:
    update_secrets(layer_name, MANUAL_SECRET_NAME, new_values)


def bulk_update_manual_secrets(layer_name: str, env_file: str) -> None:
    if not os.path.exists(env_file):
        raise UserErrors(
            f"Could not find file {env_file}"
        )
    new_values = dotenv_values(env_file)
    update_manual_secrets(layer_name, new_values)
