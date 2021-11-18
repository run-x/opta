from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.inspect_cmd import inspect
from opta.layer import Layer
from opta.module import Module
from opta.resource import Resource

REGISTRY = {
    "aws": {
        "module_aliases": [],
        "modules": {
            "fake-module": {
                "location": "fake-module",
                "inspect": {
                    "test_resource.test": {
                        "name": "Test resource",
                        "url": "https://console.aws.amazon.com/test/{test_value}?region={aws_region}",
                        "desc": "This is a test resource",
                    }
                },
            }
        },
    }
}

TERRAFORM_STATE = {
    "module.testmodule.test_resource.test": {
        "module": "module.testmodule",
        "name": "test",
        "test_value": "foobar",
        "type": "test_resource",
    }
}


def test_inspect(mocker: MockFixture) -> None:
    # Opta file check
    mocked_os_path_exists = mocker.patch("opta.utils.os.path.exists")
    mocked_os_path_exists.return_value = True

    # Mock tf file generation
    mocked_layer_class = mocker.patch("opta.commands.inspect_cmd.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocked_layer.org_name = "dummy_org_name"
    mocked_layer.name = "dummy_name"
    mocker.patch("opta.commands.inspect_cmd.gen_all")
    # Mock precheck call
    mocked_pre_check = mocker.patch("opta.commands.inspect_cmd.pre_check")
    # Mock the inspect config
    mocker.patch("opta.module.REGISTRY", REGISTRY)
    # Mock fetching the terraform state
    mocker.patch(
        "opta.commands.inspect_cmd.fetch_terraform_state_resources",
        return_value=TERRAFORM_STATE,
    )
    # Mock reading the provider's AWS region from the main tf file
    mocker.patch(
        "opta.commands.inspect_cmd.InspectCommand._get_aws_region",
        return_value="us-east-1",
    )

    # Mock reading opta resources.
    mocker.patch("opta.module.Module._read_tf_module_config")
    mocked_layer = mocker.Mock()
    mocked_layer.name = ""
    mocked_layer.cloud = "aws"
    fake_module = Module(
        data={"type": "fake-module", "name": "testmodule"}, layer=mocked_layer
    )
    fake_resource = Resource(fake_module, "test_resource", "test", {})
    mocker.patch(
        "opta.commands.inspect_cmd.InspectCommand._get_opta_config_terraform_resources",
        return_value=[fake_resource],
    )

    runner = CliRunner()
    result = runner.invoke(inspect)

    assert result.exit_code == 0
    mocked_pre_check.assert_called_once()
    # Using split to compare without whitespaces
    assert (
        result.output.split()
        == """
    NAME          DESCRIPTION             LINK
    Test resource This is a test resource https://console.aws.amazon.com/test/foobar?region=us-east-1
    """.split()
    )
