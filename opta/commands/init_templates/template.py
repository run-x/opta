import copy
from os import path
from typing import Callable, List, Optional

import yaml
from colored import attr, fg

EXAMPLES_DIR = path.dirname(__file__)


def load_template(template_type: str, template_name: str) -> dict:
    file_path = path.join(EXAMPLES_DIR, template_type, template_name, "opta.yaml")
    with open(file_path) as f:
        return yaml.safe_load(f)


class TemplateVariable:
    def __init__(
        self,
        prompt: str,  # the prompt that the user sees
        applier: Callable[[dict, str], dict],  # applies the change to a template
        validator: Optional[Callable[[str], bool]] = None,  # validates the variable
        error_message: Optional[str] = None,
    ):
        self.prompt = prompt
        self.applier = applier
        self.validator = validator
        self.error_message = error_message

    def validate(self, v: str) -> bool:
        if self.validator is None:
            return True
        return self.validator(v)

    def apply(self, d: dict, v: str) -> dict:
        return self.applier(d, v)


class Template:
    def __init__(self, template_type: str, name: str, variables: List[TemplateVariable]):
        self.initial_state = load_template(template_type, name)
        self.variables = variables
        self.name = name

    def run(self) -> dict:
        result = copy.deepcopy(self.initial_state)
        for variable in self.variables:
            success = False
            while not success:
                val = input(f"{variable.prompt}: ")
                success = variable.validate(val)
                if success:
                    result = variable.apply(result, val)
                else:
                    print(fg("red"), end="")
                    print(f"Error: {variable.error_message}")
                    print(attr("reset"), end="")

        return result
