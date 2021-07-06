from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "google", "project"])
    set_path(d, v)
    return d


gcpProjectVariable = TemplateVariable(prompt="GCP project", applier=apply,)
