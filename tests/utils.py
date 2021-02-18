import json


class MockedCmdJsonOut:
    def __init__(self, out: dict):
        self.stdout = json.dumps(out).encode("utf-8")


class MockedCmdOut:
    def __init__(self, out: str):
        self.stdout = out.encode("utf-8")
