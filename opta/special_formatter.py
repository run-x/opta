import logging
import string
from typing import Any, List

from opta.exceptions import UserErrors

logger = logging.getLogger("opta")


class PartialFormatter(string.Formatter):
    def __init__(self, missing: str = "~~", bad_fmt: str = "!!") -> None:
        self.bad_field_names: List[str] = list()
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name: str, args: Any, kwargs: Any) -> Any:
        # Handle a key not found
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            self.bad_field_names.append(field_name)
            logger.debug(
                f"Did not find field {field_name} when trying to format. Odds are "
                "this is just setting it to an empty default and you can ignore this"
            )
            val = None, field_name
        return val

    def format_field(self, value: Any, spec: Any) -> Any:
        # handle an invalid format
        if value is None:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is None:
                raise
            else:
                return self.bad_fmt

    def is_valid(self) -> None:
        log: str = "The following field names are not valid:"
        if len(self.bad_field_names) > 0:
            for bad_field_name in self.bad_field_names:
                log += f"\n\t * {bad_field_name}"
            raise UserErrors(log)
