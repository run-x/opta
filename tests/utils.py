import json
from typing import Any, List
from unittest.mock import MagicMock


class MockedCmdJsonOut:
    def __init__(self, out: dict):
        self.stdout = json.dumps(out).encode("utf-8")


class MockedCmdOut:
    def __init__(self, out: str):
        self.stdout = out.encode("utf-8")


def get_call_args(mocked_obj: MagicMock) -> List[Any]:
    raw_call_args = mocked_obj.call_args_list
    return [arg[0][0] for arg in raw_call_args]
