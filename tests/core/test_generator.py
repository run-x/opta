import json
import os

from pytest_mock import MockFixture

from opta.core.generator import gen_all
from tests.fixtures.apply import APPLY_WITHOUT_ORG_ID, BASIC_APPLY


class TestGenerator:
    def test_gen(self, mocker: MockFixture) -> None:
        mocker.patch("opta.core.generator.os.path.exists")
        mocker.patch("opta.core.generator.open")

        test_gen_file_path = "pytest_main.tf.json"
        mocker.patch("opta.core.generator.TF_FILE_PATH", test_gen_file_path)

        # Opta configs and terraform files are 1-1 mappings.
        # Make sure the expected terraform file contents are generated
        # from the opta config
        opta_config, gen_tf_file = BASIC_APPLY
        mocker.patch("opta.core.generator.yaml.load", return_value=opta_config)
        gen_all(config="", env=None)
        assert gen_tf_file == json.load(open(test_gen_file_path))

        # Make sure generation still works even when org_id is not passed.
        opta_config, gen_tf_file = APPLY_WITHOUT_ORG_ID
        mocker.patch("opta.core.generator.yaml.load", return_value=opta_config)
        gen_all(config="", env=None)
        assert gen_tf_file == json.load(open(test_gen_file_path))

        os.remove(test_gen_file_path)
