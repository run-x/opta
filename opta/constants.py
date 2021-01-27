import os

import yaml

registry_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "registry.yaml"
)
debugger_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "debugger.yaml"
)
version_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "version.txt"
)

REGISTRY = yaml.load(open(registry_path), Loader=yaml.Loader)
DEBUG_TREE = yaml.load(open(debugger_path), Loader=yaml.Loader)
VERSION = open(version_path).read()
