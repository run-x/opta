from typing import Dict, FrozenSet, Optional, Set, Union

from opta.exceptions import UserErrors
from opta.utils import is_tool

_registered_path_executables: Dict[str, Optional[str]] = {}

# TODO: In python 3.9+, switch to using collections.abc.Set
StringSetOrFrozen = Union[Set[str], FrozenSet[str]]


def ensure_installed(*names: str) -> None:
    """
    Convienince function to make calling validate_installed_path_executables easier with hardcoded names (using the `fozenset({"name"})` syntax isn't required).
    """
    validate_installed_path_executables(frozenset(names))


def get_missing_path_executables(names: StringSetOrFrozen) -> Dict[str, Optional[str]]:
    """
    Returns a dict whose keys are executables missing from the PATH, limited to `names`.
    The dict value, if not None, is the URL to the install page for that tool.
    """
    missing: Dict[str, Optional[str]] = {}

    for name in names:
        # Ensure that name is registered so we raise an exception even if the name is found on PATH
        try:
            install_url = _registered_path_executables[name]
        except KeyError:
            raise ValueError(f"{name} is not a registered path executable")

        if is_tool(name):
            continue

        missing[name] = install_url

    return missing


def register_path_executable(name: str, *, install_url: Optional[str] = None) -> None:
    """
    Registers an executable for later use in dependency checks.
    """
    if name in _registered_path_executables:
        raise ValueError(f"{name} already registered as a path executable")

    _registered_path_executables[name] = install_url


def validate_installed_path_executables(names: FrozenSet[str]) -> None:
    """Raises a UserErrors exception if any executables listed in `names` are missing from PATH"""
    missing = get_missing_path_executables(names)
    if not missing:
        return

    sorted_names = sorted(missing)

    nice_missing = [
        name + (f" (visit {missing[name]} to install)" if missing[name] else "")
        for name in sorted_names
    ]

    message = "Missing required executables on PATH: {}".format("; ".join(nice_missing))

    raise UserErrors(message)


AWS_CLI_INSTALL_URL = (
    "https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
)
AZ_CLI_INSTALL_URL = "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
DOCKER_INSTALL_URL = "https://docs.docker.com/get-docker/"
GCP_CLI_INSTALL_URL = "https://cloud.google.com/sdk/docs/install"
HELM_INSTALL_URL = "https://helm.sh/docs/intro/install/"
KUBECTL_INSTALL_URL = "https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/"
TERRAFORM_INSTALL_URL = "https://learn.hashicorp.com/tutorials/terraform/install-cli"


def _register_all() -> None:
    register_path_executable("aws", install_url=AWS_CLI_INSTALL_URL)
    register_path_executable("az", install_url=AZ_CLI_INSTALL_URL)
    register_path_executable("docker", install_url=DOCKER_INSTALL_URL)
    register_path_executable("gcloud", install_url=GCP_CLI_INSTALL_URL)
    register_path_executable("helm", install_url=HELM_INSTALL_URL)
    register_path_executable("kubectl", install_url=KUBECTL_INSTALL_URL)
    register_path_executable("terraform")


_register_all()
