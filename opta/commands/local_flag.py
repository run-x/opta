import os
from pathlib import Path
from shutil import rmtree

from ruamel import yaml

from opta.utils import logger


def _handle_local_flag(config: str, test: bool = False) -> str:
    if test:
        return config
    if "opta-local-" in config:
        return config
    logger.info("Checking local Opta Kubernetes environment, will install if needed.")

    dir_path = os.path.join(Path.home(), ".opta", "local")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(os.path.join(dir_path, "localopta.yml"), "w") as fw:
        yaml.safe_dump(
            {
                "name": "localopta",
                "org_name": "local",
                "providers": {"local": {}},
                "modules": [{"type": "local-base"}],
            },
            fw,
        )

    with open(config, "r") as fr:
        y = yaml.round_trip_load(fr, preserve_quotes=True)
    if "environments" not in y:  # This is an environment opta file, so do nothing
        return config
    y["environments"] = [{"name": "localopta", "path": dir_path + "/localopta.yml"}]
    p = Path(config)
    config = os.path.join(p.parent, "opta-local-" + p.name)
    with open(config, "w") as fw:
        yaml.round_trip_dump(y, fw, explicit_start=True)

    return config


def _clean_tf_folder() -> None:
    if os.path.isdir(os.getcwd() + "/.terraform"):
        rmtree(os.getcwd() + "/.terraform")
