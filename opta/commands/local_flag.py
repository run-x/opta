import os
from pathlib import Path
from shutil import copyfile, rmtree

from ruamel import yaml

from opta.utils import logger


def _handle_local_flag(config: str, test=False) -> str:
    if test:
        return config
    logger.info("Checking local Opta Kubernetes environment, will install if needed.")

    dir_path = os.path.join(Path.home(), ".opta", "local")
    copyfile("config/localopta.yml", dir_path + "/localopta.yml")
    with open(config, "r") as fr:
        y = yaml.load(fr)
    y["environments"] = [{"name": "localopta", "path": dir_path + "/localopta.yml"}]
    p = Path(config)
    config = os.path.join(p.parent, "opta-local-" + p.name)
    with open(config, "w") as fw:
        yaml.dump(y, fw)

    return config


def _clean_tf_folder() -> None:
    if os.path.isdir(os.getcwd() + "/.terraform"):
        rmtree(os.getcwd() + "/.terraform")
