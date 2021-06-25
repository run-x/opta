from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable
from opta.layer import Layer


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["name"])
    set_path(d, v)
    return d


nameVariable = TemplateVariable(
    prompt="name",
    applier=apply,
    validator=Layer.valid_name,
    error_message="Invalid name: can only contain letters, dashes and numbers",
)
