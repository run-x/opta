from typing import Optional

import boto3
import botocore
import yaml

from opta.layer import Layer
from opta.utils import logger


def download_state(configfile: str, env: Optional[str]) -> bool:
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

    return True
