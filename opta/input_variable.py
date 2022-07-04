from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from opta.exceptions import UserErrors


class InputVariable:
    """
    Type to handle input variables
    """

    name: str
    default: Any
    description: Optional[str]

    def __init__(self) -> None:
        self.name = ""
        self.default = None
        self.description = None

    def __repr__(self) -> str:
        args = {
            "name": self.name,
            "default": self.default,
            "description": self.description,
        }

        printed_args = ", ".join(
            f"{key}={repr(value)}" for key, value in args.items() if value
        )

        return f"Variable({printed_args})"

    @classmethod
    def from_dict(cls: Type[InputVariable], raw: dict) -> InputVariable:
        variable = cls()
        variable.name = raw["name"]
        variable.default = raw.get("default")
        variable.description = raw.get("description")

        return variable

    def to_dict(self) -> Dict[str, Any]:
        raw: Dict[str, Any] = {
            "name": self.name,
            "default": self.default,
            "description": self.description,
        }
        return raw

    @staticmethod
    def render_dict(
        input_variables: List[InputVariable],
        given_inputs: Dict[str, Any],
        strict_input_variables: bool = True,
    ) -> Dict[str, Any]:
        output = {}
        for input_variable in input_variables:
            if input_variable.name in given_inputs:
                output[input_variable.name] = given_inputs[input_variable.name]
            elif input_variable.default is not None:
                output[input_variable.name] = input_variable.default
            elif strict_input_variables:
                raise UserErrors(
                    f"Input variable {input_variable.name} was expected, but not given"
                )
        return output
