import re

from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable


def validate(account_id: str) -> bool:
    return re.match(r"^\d{12}$", account_id) is not None


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "aws", "account_id"])
    set_path(d, v)
    return d


accountIdVariable = TemplateVariable(
    prompt="AWS account id",
    applier=apply,
    validator=validate,
    error_message="invalid account id -- must be a string of 12 digits",
)
