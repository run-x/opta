import os
from pathlib import Path
from shutil import rmtree
from typing import Tuple

from ruamel import yaml


def _handle_local_flag(config: str, test: bool = False) -> Tuple[str, str]:

    with open(config, "r") as fr:
        yamlcontent = yaml.round_trip_load(fr, preserve_quotes=True)
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
        yaml.safe_dump(
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
        yaml.round_trip_dump(yamlcontent, fw, explicit_start=True)

    return config, env_yaml_path + "/localopta.yaml"


def _clean_tf_folder() -> None:
    if os.path.isdir(os.getcwd() + "/.terraform"):
        rmtree(os.getcwd() + "/.terraform")
