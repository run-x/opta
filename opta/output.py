import os  # noqa: E402
import os.path  # noqa: E402

from opta.nice_subprocess import nice_run  # noqa: E402


def get_terraform_outputs(force_init: bool = False) -> str:
    """ Fetch terraform outputs from existing TF file """
    if force_init or not _terraform_dir_exists():
        nice_run(["terraform", "init", "-reconfigure"], check=True)
    nice_run(["terraform", "get", "--update"], check=True)
    return nice_run(
        ["terraform", "output", "-json"], check=True, capture_output=True
    ).stdout.decode("utf-8")


def _terraform_dir_exists() -> bool:
    return os.path.isdir(".terraform")
