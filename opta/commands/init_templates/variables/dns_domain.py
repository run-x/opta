from opta.commands.init_templates.helpers import set_module_field
from opta.commands.init_templates.template import TemplateVariable

dnsDomainVariable = TemplateVariable(
    prompt="dns domain", applier=set_module_field("dns", ["domain"]),
)
