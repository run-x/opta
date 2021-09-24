import unittest
import os
import json

from opta.core.local import Local
from opta.layer import Layer


class LocalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.layer = Layer(
            name="testname",
            org_name="testorg",
            providers={"local": {"path": "/tmp"}},
            modules_data=[],
            path="/tmp",
            parent=None,
        )
        self.local = Local(self.layer)
        self.local.tf_file = "/tmp/tfconfig"
        self.local.config_file_path = "/tmp/localconfig"
        with open(self.local.config_file_path, "w") as f:
            json.dump({"a": "1"}, f)
        with open(self.local.tf_file, "w") as f:
            f.write("Some tf state for testing")

        return super().setUp()

    def tearDown(self) -> None:
        if os.path.isfile("/tmp/localconfig"):
            os.remove("/tmp/localconfig")
        if os.path.isfile("/tmp/tfconfig"):
            os.remove("/tmp/tfconfig")

        return super().tearDown()

    def test_get_remote_config(self):
        assert self.local.get_remote_config() == {"a": "1"}

    def test_upload_opta_config(self):
        self.local.upload_opta_config()
        dict = json.load(open(self.local.config_file_path, "r"))
        assert set(dict.keys()) == set(["opta_version", "original_spec", "date"])

    def test_delete_local_tf_state(self):
        self.local.delete_local_tf_state()
        assert os.path.isfile(self.local.tf_file) is False
