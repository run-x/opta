# new-module-api

from opta.exceptions import UserErrors
from opta.preprocessor.registry import registered
from opta.preprocessor.util import CURRENT_VERSION, DEFAULT_VERSION


def preprocess_layer(data: dict) -> None:
    version = data.setdefault("version", DEFAULT_VERSION)
    if not isinstance(version, int):
        raise UserErrors("Layer YAML version must be an int")

    if version == CURRENT_VERSION:
        return

    processors = registered()
    if version not in processors:
        raise UserErrors(f"Unsupported YAML version {version}")

    while version < CURRENT_VERSION:
        processor = processors[version]
        processor.process(data)

        new_version = data["version"]
        if new_version == version:
            raise RuntimeError(
                f"YAML preprocessor for version {version} did not update the YAML version"
            )

        if new_version < version:
            raise RuntimeError(
                f"YAML preprocessor for version {version} must not regress the YAML version"
            )

        if new_version < CURRENT_VERSION and new_version not in processors:
            raise RuntimeError(
                f"YAML preprocessor for version {version} must not return an unsupported YAML version"
            )

        version = new_version
