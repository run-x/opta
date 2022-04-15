from typing import Final, List

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors
from opta.utils import logger

# Params that are used for bring-your-own-VPC aka existing VPC.
# Order below is used when printing the mutually required params
_EXISTING_VPC_PARAMS: Final = ["vpc_id", "public_subnet_ids", "private_subnet_ids"]


class AwsBaseProcessor(ModuleProcessor):
    def process(self, module_idx: int) -> None:
        # If any of the "bring your own VPC" params are set, validate all of them
        for param in _EXISTING_VPC_PARAMS:
            if param in self.module.data:
                self.validate_existing_vpc_params(self.module.data)
                break

        super().process(module_idx)

    def validate_existing_vpc_params(self, data: dict) -> None:
        logger.debug("Validating existing VPC parameters")

        missing = [param for param in _EXISTING_VPC_PARAMS if param not in data]
        if missing:
            param_str = ", ".join(missing)
            raise UserErrors(
                f"In the aws_base module, the parameters `{param_str}` are all required if any are set"
            )

        for unique_param in ["public_subnet_ids", "private_subnet_ids"]:
            values: List[str] = data[unique_param]
            if len(values) != len(set(values)):
                raise UserErrors(
                    f"In the aws_base module, the values in {unique_param} must all be unique"
                )
