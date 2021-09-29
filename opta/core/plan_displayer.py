from typing import Any, Dict, Tuple

from colored import attr, fg
from tabulate import tabulate

from opta.constants import TF_PLAN_PATH
from opta.core.terraform import Terraform
from opta.utils import logger

LOW_RISK = "LOW"
HIGH_RISK = "HIGH"
PLAN_SEVERITIES = {LOW_RISK, HIGH_RISK}
ACTION_TO_RISK = {
    "create": LOW_RISK,
    "read": LOW_RISK,
    "delete": HIGH_RISK,
    "update": LOW_RISK,
    "replace": HIGH_RISK,
}
RISK_COLORS = {
    LOW_RISK: fg("green"),
    HIGH_RISK: fg("magenta"),
}
RISK_EXPLANATIONS = {
    LOW_RISK: (
        "This is the safe level of risk. For these changes there is no expected downtime or dataloss of any sort. "
        "You should feel confident in the changes listed here."
    ),
    HIGH_RISK: (
        "This is the high level of risk. For these changes there MAY (but not guaranteed) be some donwtime "
        "and / or dataloss."
    ),
}

LOW_RISK_FIELDS = {
    "aws_elasticache_replication_group": ["snapshot_window", "tags", "tags_all"],
    "helm_release": ["values", "timeout"],
    "aws_rds_cluster": ["backup_retention_period", "tags", "tags_all"],
    "aws_rds_cluster_instance": ["instance_class", "tags", "tags_all"],
}


def _max_risk(risk_1: str, risk_2: str) -> str:
    if HIGH_RISK in [risk_1, risk_2]:
        return HIGH_RISK
    return LOW_RISK


def dict_diffs(dict1: Dict, dict2: dict) -> Dict[Any, Tuple[Any, Any]]:
    diff_dict: Dict[Any, Tuple[Any, Any]] = {}
    for key in dict1.keys():
        if key not in dict2:
            diff_dict[key] = (dict1[key], None)
        if dict1[key] != dict2[key]:
            diff_dict[key] = (dict1[key], dict2[key])
    for key in dict2.keys():
        if key not in dict1:
            diff_dict[key] = (None, dict2[key])

    return diff_dict


class PlanDisplayer:
    @staticmethod
    def handle_update(resource_change: Dict) -> Tuple[str, str]:

        if resource_change.get("change", {}).get("resource_change", {}) != {}:
            return LOW_RISK, "refreshing data"
        if (
            resource_change["type"] == "helm_release"
            and resource_change["name"] == "k8s-service"
        ):
            return LOW_RISK, "deploying new version of app"

        diff_dict = dict_diffs(
            resource_change["change"]["before"], resource_change["change"]["after"]
        )
        high_risk_change_keys = []

        for key in diff_dict.keys():
            if key not in LOW_RISK_FIELDS.get(
                resource_change["type"], ["tags", "tags_all", "labels", "resource_labels"]
            ):
                high_risk_change_keys.append(key)

        if len(high_risk_change_keys) == 0:
            return LOW_RISK, "updating low risk fields"

        if len(high_risk_change_keys) <= 3:
            prefix = (
                "updating fields:"
                if len(high_risk_change_keys) > 1
                else "updating field:"
            )
            return HIGH_RISK, f"{prefix} {', '.join(high_risk_change_keys)}"

        return (
            HIGH_RISK,
            f"updating fields {', '.join(high_risk_change_keys[:3])}, etc...",
        )

    @staticmethod
    def display(detailed_plan: bool = False) -> None:
        if detailed_plan:
            Terraform.show(TF_PLAN_PATH)
            return
        plan_dict = Terraform.show_plan()
        plan_risk = LOW_RISK
        module_changes: dict = {}
        resource_change: dict
        for resource_change in plan_dict.get("resource_changes", []):
            if resource_change.get("change", {}).get("actions", ["no-op"]) == ["no-op"]:
                continue
            address: str = resource_change["address"]

            if not address.startswith("module."):
                logger.warn(
                    f"Unable to determine risk of changes to resource {address}. "
                    "Please run in detailed plan mode for more info"
                )
            module_name = address.split(".")[1]
            module_changes[module_name] = module_changes.get(
                module_name, {"risk": LOW_RISK, "resources": {}}
            )
            resource_name = ".".join(address.split(".")[2:])
            actions = resource_change.get("change", {}).get("actions", [])
            if "create" in actions and "delete" in actions:
                actions = ["replace"]
            action = actions[0]
            if action in ["read", "create"]:
                current_risk = LOW_RISK
                action_reason = (
                    "data_refresh" if action == "read" else "ground_up_creation"
                )
            elif action in ["replace", "destroy"]:
                current_risk = HIGH_RISK
                action_reason = resource_change.get("action_reason", "N/A")
            elif action in ["update"]:
                current_risk, action_reason = PlanDisplayer.handle_update(resource_change)
            else:
                raise Exception(f"Do not know how to handle planned action: {action}")

            module_changes[module_name]["resources"][resource_name] = {
                "action": action,
                "reason": action_reason,
                "risk": current_risk,
            }
            module_changes[module_name]["risk"] = _max_risk(
                module_changes[module_name]["risk"], current_risk
            )
            plan_risk = _max_risk(plan_risk, current_risk)

        logger.info(
            f"Identified total risk of {RISK_COLORS[plan_risk]}{plan_risk}{attr(0)}.\n"
            f"{RISK_EXPLANATIONS[plan_risk]}\n"
            "If you want extra help, please feel free to reach out to the Runx team at https://slack.opta.dev.\n"
            "Severity break down by module is as follows:"
        )
        module_changes_list = sorted(
            [(k, v) for k, v in module_changes.items()],
            key=lambda x: x[1]["risk"],
            reverse=True,
        )
        table = []
        for module_name, module_change in module_changes_list:
            resource_changes_list = sorted(
                [(k, v) for k, v in module_change["resources"].items()],
                key=lambda x: x[1]["risk"],
                reverse=True,
            )
            for resource_name, resource_change in resource_changes_list:
                current_risk = resource_change["risk"]
                table.append(
                    [
                        module_name,
                        resource_name,
                        resource_change["action"],
                        f"{RISK_COLORS[current_risk]}{current_risk}{attr(0)}",
                        resource_change["reason"].replace("_", " "),
                    ]
                )
        if len(module_changes) == 0:
            logger.info("No changes found.")
        else:
            print(
                tabulate(
                    table,
                    ["module", "resource", "action", "risk", "reason"],
                    tablefmt="fancy_grid",
                )
            )
        logger.info(
            "This concludes the plan summary. For more detail, please pass the --detailed-plan flag to your opta "
            "command!"
        )
