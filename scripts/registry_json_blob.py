import json

from opta.core.registry import make_registry_dict

if __name__ == "__main__":
    print(json.dumps(make_registry_dict()))
