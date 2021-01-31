# type: ignore
from opta.nice_subprocess import nice_run


class TestNiceRun:
    def test_echo(self):
        completed_process = nice_run(
            ["echo", "Hello world!"], check=True, capture_output=True
        )
        assert completed_process.returncode == 0
        assert completed_process.stdout.decode("ascii") == "Hello world!\n"
