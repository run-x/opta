import os
import sys
from typing import Any, Dict, Generator

from pytest import fixture
from pytest_mock import MockFixture


# Most commands require terraform init. Mock it here.
@fixture(autouse=True)
def mock_terraform_init(mocker: MockFixture) -> None:
    mocker.patch("opta.core.terraform.Terraform.init")


@fixture
def hide_debug_mode() -> Generator:
    """
    Temporarily hides that we are running in a test by unsetting sys._called_from_test and
    removing any env vars that might be used to disable reporting
    """
    # Grab original env vars
    # Not using the imported constant to prevent errors when collecting tests
    unset_environs = ["OPTA_DISABLE_REPORTING"]
    original_environs: Dict[str, Any] = {}
    for key in unset_environs:
        original_environs[key] = os.environ.pop(key, None)

    del sys._called_from_test  # type: ignore

    yield

    sys._called_from_test = True  # type: ignore

    # Restore original values
    for key, value in original_environs.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
