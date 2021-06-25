from opta.commands.init_templates.template import Template
from opta.commands.init_templates.variables.aws_account_id import accountIdVariable
from opta.commands.init_templates.variables.aws_region import awsRegionVariable
from opta.commands.init_templates.variables.dns_domain import dnsDomainVariable
from opta.commands.init_templates.variables.name import nameVariable
from opta.commands.init_templates.variables.org_name import orgNameVariable

awsTemplate = Template(
    "environment",
    "aws",
    [
        nameVariable,
        orgNameVariable,
        awsRegionVariable,
        accountIdVariable,
        dnsDomainVariable,
    ],
)
