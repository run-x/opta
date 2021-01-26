import pkgutil

import yaml

registry_data = pkgutil.get_data("opta", "registry.yaml")
debugger_data = pkgutil.get_data("opta", "debugger.yaml")

if not registry_data or not debugger_data:
    raise Exception("Data missing")

REGISTRY = yaml.load(registry_data)
DEBUG_TREE = yaml.load(debugger_data)
