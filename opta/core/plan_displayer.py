from typing import TYPE_CHECKING

from colored import attr, fg

from opta.constants import TF_PLAN_PATH
from opta.core.terraform import Terraform
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer

BENIGN_SEVERITY = "BENIGN"
MODERATE_SEVERITY = "MODERATE"
SERIOUS_SEVERITY = "SERIOUS"
PLAN_SEVERITIES = {BENIGN_SEVERITY, MODERATE_SEVERITY, SERIOUS_SEVERITY}
ACTION_TO_SEVERITY = {
    "create": BENIGN_SEVERITY,
    "read": BENIGN_SEVERITY,
    "delete": SERIOUS_SEVERITY,
    "update": MODERATE_SEVERITY,
    "replace": SERIOUS_SEVERITY,
}
SEVERITY_COLORS = {
    BENIGN_SEVERITY: fg("green"),
    MODERATE_SEVERITY: fg("yellow"),
    SERIOUS_SEVERITY: fg("magenta"),
}
SEVERITY_EXPLANATIONS = {
    BENIGN_SEVERITY: (
        "This is the lowest level of severity and it typically means that you are adding or refreshing "
        "things instead of changing and deleting things. You should feel very confident in these changes "
        "without knowing anything further."
    ),
    MODERATE_SEVERITY: (
        "This is the medium level of severity, meaning that something have been updates, but not destroyed or forced "
        "to replace (destroy and recreate). Typically, this means you updated some minor fields the yaml or updated "
        "to a new pta version and we're doing some backwards compatible changes."
    ),
    SERIOUS_SEVERITY: (
        "This is the highest level of severity and this means that either you are destroying something or made a big "
        "change which forced something to recreate (destroy and create itself). Please tread carefully and know what "
        "you are doing."
    ),
}


def _max_severity(severity_1: str, severity_2: str) -> str:
    if SERIOUS_SEVERITY in [severity_1, severity_2]:
        return SERIOUS_SEVERITY
    if MODERATE_SEVERITY in [severity_1, severity_2]:
        return MODERATE_SEVERITY
    return BENIGN_SEVERITY


class PlanDisplayer:
    def __init__(self, layer: "Layer"):
        self.layer = layer

    def display(self, detailed_plan: bool = False) -> None:
        if detailed_plan:
            Terraform.show(TF_PLAN_PATH)
            return
        plan_dict = Terraform.show_plan()
        plan_severity = BENIGN_SEVERITY
        module_changes: dict = {}
        resource_change: dict
        for resource_change in plan_dict.get("resource_changes", []):
            if resource_change.get("change", {}).get("actions", ["no-op"]) == ["no-op"]:
                continue
            address: str = resource_change["address"]

            if not address.startswith("module."):
                logger.warn(
                    f"Unable to determine severity of changes to resource {address}. "
                    "Please run in detailed plan mode for more info"
                )
            module_name = address.split(".")[1]
            module_changes[module_name] = module_changes.get(
                module_name, {"severity": BENIGN_SEVERITY, "resources": {}}
            )
            resource_name = ".".join(address.split(".")[2:])
            actions = resource_change.get("change", {}).get("actions", [])
            if "create" in actions and "delete" in actions:
                actions = ["replace"]
            action = actions[0]
            current_severity = ACTION_TO_SEVERITY[action]
            action_reason = resource_change.get("action_reason", "N/A")
            module_changes[module_name]["resources"][resource_name] = {
                "action": action,
                "reason": action_reason,
                "severity": current_severity,
            }
            module_changes[module_name]["severity"] = _max_severity(
                module_changes[module_name]["severity"], current_severity
            )
            plan_severity = _max_severity(plan_severity, current_severity)

        logger.info(
            f"Identified total severity of {SEVERITY_COLORS[plan_severity]}{plan_severity}{attr(0)}.\n"
            f"{SEVERITY_EXPLANATIONS[plan_severity]}\n"
            "If you want extra help, please feel free to reach out to the Runx team at slack.opta.dev.\n"
            "Severity break down by module is as follows:"
        )
        for module_name, module_change in module_changes.items():
            current_severity = module_change["severity"]
            logger.info(
                f"Module name: {module_name}. Severity: {SEVERITY_COLORS[current_severity]}{current_severity}{attr(0)}."
            )
            # No need to be verbose with benign changes
            if current_severity == BENIGN_SEVERITY:
                continue
            for resource_name, resource_change in module_change["resources"].items():
                current_severity = resource_change["severity"]
                logger.info(
                    f"  Resource name: {resource_name}. Action: {resource_change['action']}. "
                    f"Reason: {resource_change['reason']}. Severity: {SEVERITY_COLORS[current_severity]}{current_severity}{attr(0)}"
                )
        if len(module_changes) == 0:
            logger.info("No changes found.")
        logger.info(
            "This concludes the plan summary. For more detail, please pass the --detailed-plan flag to your opta "
            "command!"
        )
