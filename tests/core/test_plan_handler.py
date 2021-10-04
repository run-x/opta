# type: ignore
import os

from pytest_mock import MockFixture
from ruamel import yaml

from opta.core.plan_handler import PlanHandler


class TestPlanHandler:
    def test_run(self, mocker: MockFixture):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "core", "dummy_changes.yaml",
        )
        with open(path) as f:
            plan_dict = yaml.load(f)
        mocked_terraform = mocker.patch("opta.core.plan_handler.Terraform")
        mocked_terraform.show_plan.return_value = plan_dict
        plan_risk, module_changes = PlanHandler.determine_risk()
        PlanHandler.display(
            plan_risk=plan_risk, module_changes=module_changes, detailed_plan=False
        )
