from opta.commands.init_templates.template import TemplateVariable


def apply(d: dict, domain: str) -> dict:
    [dns_module] = [module for module in d["modules"] if module["type"] == "dns"]
    dns_module["domain"] = domain
    return d


dnsDomainVariable = TemplateVariable(prompt="dns domain", applier=apply,)
