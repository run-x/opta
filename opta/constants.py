import os

import yaml

registry_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "registry.yaml"
)
debugger_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "debugger.yaml"
)

REGISTRY = yaml.load(open(registry_path), Loader=yaml.Loader)
DEBUG_TREE = yaml.load(open(debugger_path), Loader=yaml.Loader)
