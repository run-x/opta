from opta.commands.init_templates.template import Template
from opta.commands.init_templates.variables.name import nameVariable

k8sServiceTemplate = Template("service", "k8s", [nameVariable])
