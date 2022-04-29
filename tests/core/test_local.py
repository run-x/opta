import json
import os
import unittest

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
            json.dump(
                {
                    "opta_version": "dev",
                    "date": "2021-11-15T18:26:47.553097",
                    "original_spec": "",
                    "defaults": {},
                },
                f,
            )
        with open(self.local.tf_file, "w") as f:
            f.write("Some tf state for testing")

        return super().setUp()

    def tearDown(self) -> None:
        if os.path.isfile("/tmp/localconfig"):
            os.remove("/tmp/localconfig")
        if os.path.isfile("/tmp/tfconfig"):
            os.remove("/tmp/tfconfig")

        return super().tearDown()

    def test_get_remote_config(self) -> None:
        assert self.local.get_remote_config() == {
            "opta_version": "dev",
            "date": "2021-11-15T18:26:47.553097",
            "original_spec": "",
            "defaults": {},
        }

    def test_upload_opta_config(self) -> None:
        self.local.upload_opta_config()
        with open(self.local.config_file_path) as f:
            dict = json.load(f)
        assert set(dict.keys()) == set(
            ["opta_version", "original_spec", "date", "defaults"]
        )

    def test_delete_remote_state(self) -> None:
        self.local.delete_remote_state()
        assert os.path.isfile(self.local.tf_file) is False
