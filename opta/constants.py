import os

import yaml

REGISTRY = yaml.load(
    open(f"{os.path.dirname(__file__)}/../registry.yaml"), Loader=yaml.Loader
)
