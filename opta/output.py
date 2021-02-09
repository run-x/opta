import json
import os  # noqa: E402
import os.path  # noqa: E402

from opta.nice_subprocess import nice_run  # noqa: E402
from opta.utils import deep_merge


def get_terraform_outputs(force_init: bool = False, include_parent: bool = False) -> dict:
    """ Fetch terraform outputs from existing TF file """
    if force_init or not _terraform_dir_exists():
        nice_run(["terraform", "init"], check=True)

    outputs = _fetch_current_outputs()

    if include_parent:
        outputs = deep_merge(outputs, _fetch_parent_outputs())

    return outputs


def _terraform_dir_exists() -> bool:
    return os.path.isdir(".terraform")


def _fetch_current_outputs() -> dict:
    current_state_outputs_raw = nice_run(
        ["terraform", "output", "-json"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    return json.loads(current_state_outputs_raw)


def _fetch_parent_outputs() -> dict:
    # Fetch the terraform state
    out = nice_run(["terraform", "show", "-json"], check=True, capture_output=True)
    raw_data = out.stdout.decode("utf-8")
    data = json.loads(raw_data)

    # Fetch any parent remote states
    root_module = data.get("values", {}).get("root_module", {})
    resources = root_module.get("resources", [])
    parent_states = [
        resource
        for resource in resources
        if resource.get("type") == "terraform_remote_state"
    ]

    # Grab all outputs from each remote state and save it.
    parent_state_outputs = {}
    for parent in parent_states:
        parent_outputs = parent.get("values", {}).get("outputs", {})
        for k, v in parent_outputs.items():
            parent_name = parent.get("name")
            output_name = f"{parent_name}.{k}"
            parent_state_outputs[output_name] = v

    return parent_state_outputs
