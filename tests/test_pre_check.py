from pytest_mock import MockFixture

from opta.pre_check import dependency_check


class TestPreCheck:
    def test_dependency_check(self, mocker: MockFixture) -> None:
        validate_version = mocker.patch("opta.pre_check.Terraform.validate_version")

        dependency_check()

        validate_version.assert_called_once()
