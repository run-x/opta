from string import Formatter

from opta.preprocessor.util import ModuleHandler, VersionProcessor
from opta.utils.ref import Reference, ReferenceParseError
from opta.utils.visit import Visitor


def reformat_interpolation_deep(data: dict) -> None:
    """
    Reformats all interpolated strings (`{foo}`) into the new interpolation format
    """
    visitor = Visitor(data)

    skip_fields = [
        Reference("type"),
    ]

    for ref, value in visitor:
        if not ref or ref in skip_fields:
            continue

        if not isinstance(value, str):
            continue

        new_value = reformat_interpolation(value)
        if new_value == value:
            continue

        visitor[ref] = new_value


def reformat_interpolation(input: str) -> str:
    formatter = Formatter()

    output = []
    for literal, field_name, format_spec, conversion in formatter.parse(input):
        output.append(literal)

        if not field_name:
            continue

        if format_spec:
            raise ValueError("format_spec in formatted string not supported")

        if conversion:
            raise ValueError("conversion field in formatted string not supported")

        try:
            Reference.parse(field_name)
        except ReferenceParseError:
            raise ValueError(f"invalid reference value: {field_name}")

        new_syntax = "${" + field_name + "}"
        output.append(new_syntax)

    return "".join(output)


V1 = VersionProcessor(versions=1, handlers=[ModuleHandler(reformat_interpolation_deep)])
