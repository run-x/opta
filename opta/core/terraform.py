from typing import List, Optional, Set

import boto3
import botocore
import yaml

from opta.layer import Layer
from opta.nice_subprocess import nice_run
from opta.utils import logger


class Terraform:
    # True if terraform.tfstate is downloaded.
    downloaded_state = False

    @classmethod
    def init(cls) -> None:
        nice_run(["terraform", "init"], check=True)

    @classmethod
    def apply(cls, *tf_flags: List[str]) -> None:
        cls.init()
        nice_run(["terraform", "apply", *tf_flags], check=True)

    @classmethod
    def plan(cls, *tf_flags: List[str]) -> None:
        cls.init()
        nice_run(["terraform", "plan", *tf_flags], check=True)

    @classmethod
    def get_existing_modules(cls, configfile: str, env: Optional[str]) -> Set[str]:
        existing_resources = cls.get_existing_resources(configfile, env)
        module_resources = [r for r in existing_resources if r.startswith("module")]
        return set(map(lambda r: r.split(".")[1], module_resources))

    @classmethod
    def get_existing_resources(cls, configfile: str, env: Optional[str]) -> List[str]:
        if not cls.downloaded_state:
            success = cls.download_state(configfile, env)
            if not success:
                logger.info(
                    "Could not fetch remote terraform state, assuming no resources exist yet."
                )
                return []

        return (
            nice_run(["terraform", "state", "list"], check=True, capture_output=True)
            .stdout.decode("utf-8")
            .split("\n")
        )

    @classmethod
    def download_state(cls, configfile: str, env: Optional[str]) -> bool:
        cls.init()
        conf = yaml.load(open(configfile), Loader=yaml.Loader)
        layer = Layer.load_from_dict(conf, env)

        providers = layer.gen_providers(0, True)
        if "s3" in providers.get("terraform", {}).get("backend", {}):
            bucket = providers["terraform"]["backend"]["s3"]["bucket"]
            key = providers["terraform"]["backend"]["s3"]["key"]
            logger.debug(
                f"Found an s3 backend in bucket {bucket} and key {key}, "
                "gonna try to download the statefile from there"
            )
            s3 = boto3.client("s3")
            try:
                s3.download_file(bucket, key, "./terraform.tfstate")
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    # The object does not exist.
                    return False
                raise

        cls.downloaded_state = True
        return True
