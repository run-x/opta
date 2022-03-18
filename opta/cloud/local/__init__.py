# new-module-api

from opta.cloud.registry import Registry

from .state import LocalStore

__all__ = ["LocalStore"]


def register(registry: Registry) -> None:
    registry.register_state_store("local", LocalStore)
