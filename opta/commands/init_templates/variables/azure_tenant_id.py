from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "azurerm", "tenant_id"])
    set_path(d, v)
    return d


azureTenantIdVariant = TemplateVariable(
    prompt="Azure tenant ID (see https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-create-new-tenant)",
    applier=apply,
)
