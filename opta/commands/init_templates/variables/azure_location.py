from opta.commands.init_templates.helpers import dictionary_deep_set
from opta.commands.init_templates.template import TemplateVariable

LOCATIONS = [
    "australiaeast",
    "brazilsouth",
    "canadacentral",
    "centralus",
    "eastus",
    "eastus2",
    "francecentral",
    "germanywestcentral",
    "japaneast",
    "southafricanorth",
    "southcentralus",
    "southeastasia",
    "uksouth",
    "westeurope",
    "westus2",
    "westus3",
]


def validate(location_name: str) -> bool:
    return location_name in LOCATIONS


def apply(d: dict, v: str) -> dict:
    set_path = dictionary_deep_set(["providers", "azurerm", "location"])
    set_path(d, v)
    return d


indented_locations = [f"\t{location}" for location in LOCATIONS]
location_string = "\n".join(indented_locations)


azureLocationVariable = TemplateVariable(
    prompt="Azure location",
    applier=apply,
    validator=validate,
    error_message=f"Must be one of\n{location_string}",
    default_value="centralus",
)
