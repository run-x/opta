from opta.commands.init_templates.template import Template
from opta.commands.init_templates.variables.azure_location import azureLocationVariable
from opta.commands.init_templates.variables.azure_subscription_id import (
    azureSubscriptionIdVariable,
)
from opta.commands.init_templates.variables.azure_tenant_id import azureTenantIdVariant
from opta.commands.init_templates.variables.name import nameVariable
from opta.commands.init_templates.variables.org_name import orgNameVariable

azureTemplate = Template(
    "environment",
    "azure",
    [
        nameVariable,
        orgNameVariable,
        azureLocationVariable,
        azureTenantIdVariant,
        azureSubscriptionIdVariable,
    ],
)
