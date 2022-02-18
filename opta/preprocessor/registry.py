# new-module-api

from typing import Dict

from opta.preprocessor.util import VersionProcessor
from opta.preprocessor.v1 import V1

RegistryType = Dict[int, VersionProcessor]

_version_processors: RegistryType = {}


def register_single(version: int, processor: VersionProcessor) -> None:
    if version in _version_processors:
        raise ValueError(f"Version {version} already has a registered preprocessor")

    _version_processors[version] = processor


def register(processor: VersionProcessor) -> None:
    for version in processor.versions:
        register_single(version, processor)


def register_all() -> None:
    register(V1)


def registered() -> RegistryType:
    if not _version_processors:
        register_all()

    return _version_processors.copy()
