import os
from pathlib import Path
from shutil import rmtree
from typing import Tuple

from opta.utils.yaml import YAML


def _handle_local_flag(config: str, test: bool = False) -> Tuple[str, str]:

    with open(config, "r") as fr:
        yamlcontent = YAML.round_trip().load(fr)
        if "org_name" in yamlcontent:
            org_name = yamlcontent["org_name"]
        else:
            org_name = "localorg"
    env_yaml_path = os.path.join(Path.home(), ".opta", "local", org_name)
    if test:
        return config, env_yaml_path + "/localopta.yaml"
    if "opta-local-" in config:
        return config, env_yaml_path + "/localopta.yaml"

    if not os.path.exists(env_yaml_path):
        os.makedirs(os.path.abspath(env_yaml_path))
    with open(env_yaml_path + "/localopta.yaml", "w") as fw:
        YAML().dump(
            {
                "name": "localopta",
                "org_name": org_name,
                "providers": {"local": {}},
                "modules": [{"type": "local-base"}],
            },
            fw,
        )
    yamlcontent["environments"] = [
        {"name": "localopta", "path": env_yaml_path + "/localopta.yaml"}
    ]
    yamlcontent.pop("org_name", None)
    yamlpath = Path(config)
    config = os.path.join(yamlpath.parent, "opta-local-" + yamlpath.name)
    with open(config, "w") as fw:
        yaml = YAML.round_trip()
        yaml.explicit_start = True
        yaml.dump(yamlcontent, fw)

    return config, env_yaml_path + "/localopta.yaml"


def _clean_tf_folder() -> None:
    _clean_folder(os.getcwd() + "/.terraform")


def _clean_folder(path: str) -> None:
    if os.path.isdir(path):
        rmtree(path)
