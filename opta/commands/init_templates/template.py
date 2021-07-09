import copy
from os import path
from typing import Any, Callable, List, Optional

import yaml
from colored import attr, fg

from opta.constants import init_template_path


def load_template(template_type: str, template_name: str) -> dict:
    file_path = path.join(init_template_path, template_type, f"{template_name}.yaml")
    with open(file_path) as f:
        return yaml.safe_load(f)


class TemplateVariable:
    def __init__(
        self,
        prompt: str,  # the prompt that the user sees
        applier: Callable[[dict, str], dict],  # applies the change to a template
        validator: Optional[Callable[[str], bool]] = None,  # validates the variable
        error_message: Optional[str] = None,
        default_value: Optional[Any] = None,
    ):
        self.prompt = prompt
        self.applier = applier
        self.validator = validator
        self.error_message = error_message
        self.default_value = default_value

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
                if variable.default_value:
                    val = (
                        input(f"{variable.prompt}: ({variable.default_value}) ").strip()
                        or variable.default_value
                    )
                else:
                    val = input(f"{variable.prompt}: ").strip()
                success = variable.validate(val)
                if success:
                    result = variable.apply(result, val)
                else:
                    print(fg("red"), end="")
                    print(f"Error: {variable.error_message}")
                    print(attr("reset"), end="")

        return result
