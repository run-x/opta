from typing import Dict, Optional

import click

from opta.layer import Layer
from opta.utils import check_opta_file_exists
from opta.utils.clickoptions import config_option, env_option, input_variable_option


@click.command(hidden=True)
@config_option
@env_option
@input_variable_option
@click.option(
    "--json-schema", default=False, help="Validate using JSON schema instead of Yamale"
)
def validate(
    config: str, json_schema: bool, env: Optional[str], var: Dict[str, str]
) -> None:
    config = check_opta_file_exists(config)

    Layer.load_from_yaml(
        config, env, json_schema, input_variables=var, strict_input_variables=False
    )
