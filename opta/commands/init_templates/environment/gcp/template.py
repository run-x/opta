from opta.commands.init_templates.template import Template
from opta.commands.init_templates.variables.dns_domain import dnsDomainVariable
from opta.commands.init_templates.variables.gcp_project import gcpProjectVariable
from opta.commands.init_templates.variables.gcp_region import gcpRegionVariable
from opta.commands.init_templates.variables.name import nameVariable
from opta.commands.init_templates.variables.org_name import orgNameVariable

gcpTemplate = Template(
    "environment",
    "gcp",
    [
        nameVariable,
        orgNameVariable,
        gcpRegionVariable,
        gcpProjectVariable,
        dnsDomainVariable,
    ],
)
