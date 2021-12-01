from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "azurerm", "subscription_id"])
    set_path(d, v)
    return d


azureSubscriptionIdVariable = TemplateVariable(
    prompt="Azure subscription ID", applier=apply,
)
