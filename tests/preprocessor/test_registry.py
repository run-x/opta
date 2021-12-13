from typing import Generator

import pytest

from opta.preprocessor import registry
from opta.preprocessor.util import CURRENT_VERSION, DEFAULT_VERSION


class TestRegistry:
    def test_versions(self) -> None:
        assert (
            DEFAULT_VERSION == CURRENT_VERSION
            or DEFAULT_VERSION in registry._version_processors
        )

    def test_version_processors(self) -> None:
        # Make sure that all versions in dict are valid
        for version in registry._version_processors:
            assert 0 < version < CURRENT_VERSION

        # Make sure we aren't skipping any versions
        for version in range(1, CURRENT_VERSION):
            assert version in registry._version_processors

    @pytest.fixture(autouse=True)
    def registered_processors(self) -> Generator:
        old = registry._version_processors
        registry._version_processors = {}
        registry.register_all()

        yield

        registry._version_processors = old
