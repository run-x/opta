# type: ignore
import os

from pytest_mock import MockFixture
from ruamel import yaml

from opta.core.plan_displayer import PlanDisplayer


class TestPlanDisplayer:
    def test_run(self, mocker: MockFixture):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "core", "dummy_changes.yaml",
        )
        with open(path) as f:
            plan_dict = yaml.load(f)
        mocked_terraform = mocker.patch("opta.core.plan_displayer.Terraform")
        mocked_terraform.show_plan.return_value = plan_dict
        PlanDisplayer.display()
