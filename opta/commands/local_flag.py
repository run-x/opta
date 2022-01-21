import os
from pathlib import Path
from shutil import rmtree

from ruamel import yaml
from typing import Tuple
from opta.utils import logger

def _handle_local_flag(config: str, test: bool = False) -> Tuple[str,str]:
    if test:
        return config
    with open(config, "r") as fr:
        y = yaml.round_trip_load(fr, preserve_quotes=True)
        if "org_name" in y:
            org_name = y["org_name"]
        else:
            org_name = "localorg"

    if "opta-local-" in config:
        return config
    
    env_yaml_path = os.path.join(Path.home(), ".opta", "local", org_name)
    if not os.path.exists(env_yaml_path):
        os.makedirs(os.path.abspath(env_yaml_path))
    with open(env_yaml_path + "/localopta.yaml", "w") as fw:
        yaml.safe_dump(
            {
                "name": "localopta",
                "org_name": org_name,
                "providers": {"local": {}},
                "modules": [{"type": "local-base"}],
            },
            fw,
        )
    y["environments"] = [{"name": "localopta", "path": env_yaml_path + "/localopta.yaml"}]
    y.pop("org_name", None)
    p = Path(config)
    config = os.path.join(env_yaml_path, "opta-local-" + p.name)
    with open(config, "w") as fw:
        yaml.round_trip_dump(y, fw, explicit_start=True)

    return config, env_yaml_path + "/localopta.yaml"


def _clean_tf_folder() -> None:
    if os.path.isdir(os.getcwd() + "/.terraform"):
        rmtree(os.getcwd() + "/.terraform")
