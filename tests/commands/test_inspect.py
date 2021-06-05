from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.commands.inspect_cmd import inspect
from opta.layer import Layer
from opta.module import Module
from opta.resource import Resource

REGISTRY = {
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
    # Mock tf file generation
    mocked_layer_class = mocker.patch("opta.commands.inspect_cmd.Layer")
    mocked_layer = mocker.Mock(spec=Layer)
    mocked_layer.cloud = "aws"
    mocked_layer_class.load_from_yaml.return_value = mocked_layer
    mocker.patch("opta.commands.inspect_cmd.gen_all")
    # Mock that the terraform CLI tool exists.
    mocker.patch("opta.commands.inspect_cmd.is_tool", return_value=True)
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
    # Using split to compare without whitespaces
    assert (
        result.output.split()
        == """
    NAME          DESCRIPTION             LINK
    Test resource This is a test resource https://console.aws.amazon.com/test/foobar?region=us-east-1
    """.split()
    )
