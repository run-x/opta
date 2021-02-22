import os
import os.path
from unittest.mock import ANY, call

from click.testing import CliRunner
from pytest_mock import MockFixture

from opta.cli import _cleanup, apply
from opta.constants import TF_FILE_PATH
from opta.layer import Layer
from opta.module import Module
from opta.sentry import at_exit_callback


class TestCLI:
    def test_cleanup(self) -> None:
        with open(TF_FILE_PATH, "w") as f:
            f.write("blah")
        _cleanup()
        assert not os.path.exists(TF_FILE_PATH)

    def test_at_exit_callback_with_pending(self, mocker: MockFixture) -> None:
        mocked_write = mocker.patch("opta.cli.sys.stderr.write")
        mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
        at_exit_callback(1, 1)
        mocked_write.assert_has_calls(
            [call(mocker.ANY), call(mocker.ANY), call(mocker.ANY)]
        )
        mocked_flush.assert_called_once_with()

    def test_at_exit_callback_without_pending(self, mocker: MockFixture) -> None:
        mocked_write = mocker.patch("opta.cli.sys.stderr.write")
        mocked_flush = mocker.patch("opta.cli.sys.stderr.flush")
        at_exit_callback(0, 1)
        mocked_write.assert_not_called()
        mocked_flush.assert_called_once_with()

    def test_apply(self, mocker: MockFixture) -> None:
        mocker.patch("opta.cli.is_tool", return_value=True)
        mocker.patch("opta.cli.amplitude_client.send_event")

        mocked_layer_class = mocker.patch("opta.cli.Layer")
        mocked_layer = mocker.Mock(spec=Layer)
        mocked_layer.variables = {}
        mocked_layer_class.load_from_yaml.return_value = mocked_layer

        # Mock remote state
        mocker.patch(
            "opta.cli.Terraform.get_existing_modules", return_value={"deleted_module"}
        )

        # Mock opta config
        fake_module = Module("test", data={"type": "k8s-service", "name": "fake_module"})
        mocker.patch("opta.cli.gen", return_value=iter([(0, [fake_module], 1)]))
        tf_apply = mocker.patch("opta.cli.Terraform.apply")
        tf_create_storage = mocker.patch("opta.cli.Terraform.create_state_storage")

        # Terraform apply should be called with the configured module (fake_module) and the remote state
        # module (deleted_module) as targets.
        runner = CliRunner()
        result = runner.invoke(apply)
        print(result.output)
        assert result.exit_code == 0
        tf_apply.assert_called_once_with(
            ANY, "-target=module.deleted_module", "-target=module.fake_module"
        )
        tf_create_storage.assert_called_once_with(mocked_layer)
