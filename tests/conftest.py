from pytest import fixture
from pytest_mock import MockFixture


# Most commands require terraform init. Mock it here.
@fixture(autouse=True)
def mock_terraform_init(mocker: MockFixture) -> None:
    mocker.patch("opta.core.terraform.Terraform.init")
