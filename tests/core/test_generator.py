import json
import os

import pytest
from pytest_mock import MockFixture

from opta.constants import tf_modules_path
from opta.core.generator import gen_all, gen_opta_resource_tags
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

    def test_gen_resource_tags(self, mocker: MockFixture) -> None:
        gen_tags_file = "pytest-override.tf.json"
        mocker.patch("opta.module.TAGS_OVERRIDE_FILE", gen_tags_file)
        gen_tags_file_path = os.path.join(tf_modules_path, "aws-base", gen_tags_file)

        mocker.patch("opta.layer.open")
        mocker.patch("opta.layer.os.path.exists")

        opta_config, gen_tf_file = BASIC_APPLY
        opta_config = opta_config.copy()
        mocker.patch("opta.layer.yaml.load", return_value=opta_config)
        layer = Layer.load_from_yaml("", None)

        gen_opta_resource_tags(layer)
        tags_config = json.load(open(gen_tags_file_path))

        has_vpc = False
        for resource in tags_config["resource"]:
            resource_type = list(resource.keys())[0]
            print(resource_type)
            if resource_type == "aws_vpc":
                has_vpc = True
                assert resource[resource_type]["vpc"]["tags"]["opta"] == "true"

        assert has_vpc
        os.remove(gen_tags_file_path)
