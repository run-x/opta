# type: ignore
import unittest

import pytest

from opta.constants import DEBUG_TREE
from opta.debugger import Debugger


@pytest.fixture
def debugger():
    return Debugger()


class TestDebugger:
    def test_current_context(self, debugger):
        unittest.TestCase().assertDictEqual(debugger.current_context(), DEBUG_TREE)
        for idx, _ in enumerate(debugger.current_context().get("children", [])):
            debugger.path.append(idx)
            unittest.TestCase().assertDictEqual(
                debugger.current_context(), DEBUG_TREE["children"][idx]
            )
            debugger.path.pop()

    def test_run_loop(self, debugger):
        pass
