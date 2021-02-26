import json
import os

import pytest
from pytest_mock import MockFixture

from opta.core.generator import gen_all
from opta.exceptions import UserErrors
from opta.layer import Layer
from tests.fixtures.basic_apply import BASIC_APPLY


class TestGenerator:
    def test_gen(self, mocker: MockFixture) -> None:
        mocker.patch("opta.layer.open")
        mocker.patch("opta.layer.os.path.exists")

        test_gen_file_path = "pytest_main.tf.json"
        mocker.patch("opta.core.generator.TF_FILE_PATH", test_gen_file_path)

        # Opta configs and terraform files are 1-1 mappings.
        # Make sure the expected terraform file contents are generated
        # from the opta config
        opta_config, gen_tf_file = BASIC_APPLY
        opta_config = opta_config.copy()
        mocker.patch("opta.layer.yaml.load", return_value=opta_config)
        layer = Layer.load_from_yaml("", None)
        gen_all(layer)
        print(json.load(open(test_gen_file_path)))
        assert gen_tf_file == json.load(open(test_gen_file_path))

        # Make sure generation does not work without org name.

        opta_config, _ = BASIC_APPLY
        opta_config = opta_config.copy()
        del opta_config["org_name"]
        mocker.patch("opta.layer.yaml.load", return_value=opta_config)
        with pytest.raises(UserErrors):
            Layer.load_from_yaml("", None)

        os.remove(test_gen_file_path)
