import os

import yaml

REGISTRY = yaml.load(
    open(f"{os.path.dirname(__file__)}/../registry.yaml"), Loader=yaml.Loader
)

DEBUG_TREE = yaml.load(
    open(f"{os.path.dirname(__file__)}/../debugger.yaml"), Loader=yaml.Loader
)
