# type: ignore
from click.testing import CliRunner

from opta.version import version


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(version, [])
    assert result.exit_code == 0
