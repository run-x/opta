from typing import Set

from colored import attr, fg

from opta.exceptions import UserErrors


class Interpolation:
    bad_field_names: Set[str] = set()

    @classmethod
    def bad_fields_present(cls) -> None:
        if not cls.bad_field_names:
            return
        error = "Following field names could not be interpolated:"
        for bad_field_name in cls.bad_field_names:
            error += f"\n  * {bad_field_name}"

        raise UserErrors(f"{fg('red')}{error}{attr(0)}")

    @classmethod
    def add(cls, field_name: str) -> None:
        cls.bad_field_names.add(field_name)

    @classmethod
    def unset(cls) -> None:
        cls.bad_field_names.clear()


class OptaUpgrade:
    successful = False

    @classmethod
    def success(cls) -> None:
        cls.successful = True

    @classmethod
    def unset(cls) -> None:
        cls.successful = False
