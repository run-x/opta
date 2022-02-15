import os
import unittest

import yaml

from opta.commands.local_flag import _handle_local_flag


class Local_Flag_Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.serviceconfig = "/tmp/test_local_flag.yaml"
        self.derivedconfig = os.path.join("/tmp", "opta-local-test_local_flag.yaml")
        with open(self.serviceconfig, "w") as fw:
            yaml.dump(
                {
                    "name": "helloworld",
                    "org_name": "whatever",
                    "modules": [
                        {
                            "name": "firstapp",
                            "type": "k8s-service",
                            "port": {"http": 80},
                            "image": "docker.io/kennethreitz/httpbin:latest",
                            "healthcheck_path": "/get",
                            "links": ["sessionstore", "database"],
                            "public_uri": "/",
                        },
                        {"name": "sessionstore", "type": "redis"},
                        {"name": "database", "type": "postgres"},
                    ],
                },
                fw,
            )
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.isfile(self.serviceconfig):
            os.remove(self.serviceconfig)
        if os.path.isfile(self.derivedconfig):
            os.remove(self.derivedconfig)
        return super().tearDown()

    def test_handle_local_flag(self) -> None:
        _handle_local_flag(self.serviceconfig)
        with open(self.derivedconfig, "r") as fr:
            y = yaml.safe_load(fr)
            assert "environments" in y
            assert y["environments"][0]["name"] == "localopta"
