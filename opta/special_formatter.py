import logging
import string
from typing import Any

logger = logging.getLogger("opta")


class PartialFormatter(string.Formatter):
    def __init__(self, missing: str = "~~", bad_fmt: str = "!!") -> None:
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name: str, args: Any, kwargs: Any) -> Any:
        # Handle a key not found
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            logger.info(
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
