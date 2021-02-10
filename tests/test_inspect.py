from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import inspect
from tests.test_output import MockedCmdOut

FAKE_INSPECT_CONFIG = {
    "resources": {
        "test_resource.test": {
            "name": "Test resource",
            "url": "https://console.aws.amazon.com/test/{test_value}?region={aws_region}",
            "desc": "This is a test resource",
        }
    }
}

FAKE_TF_STATE = {
    "values": {
        "root_module": {
            "resources": [],
            "child_modules": [
                {
                    "resources": [
                        {
                            "address": "module.test_module.test_resource.test",
                            "type": "test_resource",
                            "name": "test",
                            "values": {"test_value": "foobar"},
                        }
                    ]
                }
            ],
        }
    }
}


class TestInspect:
    def test_inspect(self, mocker: MockFixture) -> None:
        mocker.patch("opta.cli.apply")
        # Mock that the terraform CLI tool exists.
        mocker.patch("opta.inspect_cmd.is_tool", return_value=True)
        # Mock the inspect config
        mocker.patch(
            "opta.inspect_cmd._read_inspect_config_file", return_value=FAKE_INSPECT_CONFIG
        )
        # Mock fetching the terraform state
        mocker.patch(
            "opta.inspect_cmd.nice_run", return_value=MockedCmdOut(FAKE_TF_STATE)
        )
        # Mock reading the provider's AWS region from the main tf file
        mocker.patch("opta.inspect_cmd._get_aws_region", return_value="us-east-1")

        runner = CliRunner()
        result = runner.invoke(inspect, [])
        print(result.exception)
        assert result.exit_code == 0
        # Using split to compare without whitespaces
        assert (
            result.output.split()
            == """
        NAME          DESCRIPTION             LINK
        Test resource This is a test resource https://console.aws.amazon.com/test/foobar?region=us-east-1
        """.split()
        )
