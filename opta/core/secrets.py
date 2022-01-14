

import os
from opta.core.kubernetes import get_namespaced_secrets, update_secrets
from opta.exceptions import UserErrors
from opta.utils import deep_merge


MANUAL_SECRET_NAME = "manual-secrets"
LINKED_SECRET_NAME = "secret"


def get_secrets(layer_name: str) -> dict:
    return deep_merge(get_manual_secrets(layer_name), get_linked_secrets(layer_name))


def get_manual_secrets(layer_name: str) -> dict:
    return get_namespaced_secrets(layer_name, MANUAL_SECRET_NAME)


def get_linked_secrets(layer_name: str) -> dict:
    return get_namespaced_secrets(layer_name, LINKED_SECRET_NAME)


