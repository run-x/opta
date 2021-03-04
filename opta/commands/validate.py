from typing import Any, Dict

import click
import yamale

from opta.constants import schema_path

schema = yamale.make_schema(schema_path)


def validate_dict(conf: Dict[Any, Any]) -> None:
    yamale.validate(schema, conf)


def validate_yaml(config_file_path: str) -> None:
    data = yamale.make_data(config_file_path)
    yamale.validate(schema, data)


@click.command()
@click.option("-c", "--config", default="opta.yml", help="Opta config file.")
def validate(config: str) -> None:
    validate_yaml(config)
