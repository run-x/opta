from __future__ import annotations

import functools
import re
from collections import abc
from typing import Any, Iterable, Iterator, Sequence, Tuple, TypeVar, Union, overload

from opta.utils.yaml import register_yaml_class

_PART_REGEX = re.compile(r"[a-z]([a-z0-9_]*[a-z0-9])?", re.IGNORECASE)
_INTERPOLATION_REGEX = re.compile(
    r"\$\{(" + _PART_REGEX.pattern + r"(?:\." + _PART_REGEX.pattern + r")*)\}",
    re.IGNORECASE,
)
_LITERAL_REGEX = re.compile(r"[a-z_][a-z0-9_].+",re.IGNORECASE)

PathElement = Union[str, int]
TRef = TypeVar("TRef", bound="Reference")


class ReferenceParseError(ValueError):
    pass


@functools.total_ordering
class Reference(Sequence):
    __slots__ = ("_path",)

    def __init__(self, *path: PathElement, skip_validation: bool = False) -> None:
        self._path: Tuple[PathElement, ...] = path or tuple()

        if not skip_validation:
            self._validate_path()

    def __str__(self) -> str:
        return ".".join(str(p) for p in self.path)

    def __repr__(self) -> str:
        cls = type(self).__name__

        return f"{cls}(*{self._path})"

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Reference):
            return NotImplemented

        return self._path < other.path

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Reference):
            return NotImplemented

        return self._path == other._path

    @overload
    def __getitem__(self, idx: int) -> PathElement:
        ...

    @overload
    def __getitem__(self: TRef, idx: slice) -> TRef:
        ...

    def __getitem__(self: TRef, idx: Union[int, slice]) -> Union[PathElement, TRef]:
        if isinstance(idx, int):
            return self._path[idx]
        elif isinstance(idx, slice):
            cls = type(self)

            return cls(*self._path[idx])

        raise TypeError(f"unsupported type for idx: {type(idx).__name__}")

    def __iter__(self) -> Iterator[PathElement]:
        return iter(self._path)

    def __len__(self) -> int:
        return len(self._path)

    def __hash__(self) -> int:
        return hash(str(self))

    def __add__(self: TRef, other: Union[Reference, Iterable[PathElement]]) -> TRef:
        # TODO: In python 3.10, replace this with isinstance(other, PathElement)
        def ispathelement(x: Any) -> bool:
            return isinstance(x, str) or isinstance(x, int)

        if isinstance(other, Reference):
            return self.join(other)
        elif isinstance(other, abc.Iterable) and all(ispathelement(x) for x in other):
            return self.child(*other)

        return NotImplemented

    def child(self: TRef, *parts: PathElement) -> TRef:
        cls = type(self)

        return cls(*self._path, *parts)

    def join(self: TRef, other: Reference) -> TRef:
        return self.child(*other._path)

    @property
    def path(self) -> Tuple[PathElement, ...]:
        return self._path

    @classmethod
    def parse(cls, raw: str) -> Reference:
        # TODO: Parse array subscript syntax
        parts = raw.split(".")

        try:
            ref = cls(*parts)
        except ValueError as e:
            raise ReferenceParseError(str(e)) from e

        return ref

    def _validate_path(self) -> None:
        for idx, part in enumerate(self._path):
            if isinstance(part, int):
                if part < 0:
                    raise ValueError(f"Path part {idx} must be non-negative")
            elif isinstance(part, str):
                if not _PART_REGEX.fullmatch(part):
                    raise ValueError(f"Path part {idx} invalid: {part}")
            else:
                raise TypeError(f"unsupported part type {type(part).__name__}")


class InterpolatedReference(Reference):
    """
    A reference that was created using an interpoliation string. Can be serialized to/from YAML
    """

    yaml_tag = "!ref"

    def __str__(self) -> str:
        return "${%s}" % self._inner_str()

    def _inner_str(self) -> str:
        return super().__str__()

    @classmethod
    def parse(cls, raw: str) -> InterpolatedReference:
        match = _INTERPOLATION_REGEX.fullmatch(raw)
        if not match:
            raise ReferenceParseError("`raw` not an interpolated string")

        return cls.parse_dotted(match[1])

    @classmethod
    def parse_dotted(cls, raw: str) -> InterpolatedReference:
        parsed = super().parse(raw)

        # Ideally, we would just return `parsed`, but the type system makes that difficult
        return cls(*parsed.path)

    @classmethod
    def to_yaml(cls, representer: Any, node: InterpolatedReference) -> Any:
        # TODO: Do we need to be able to dump this class to YAML?
        return representer.represent_scalar(cls.yaml_tag, node._inner_str())

    @classmethod
    def from_yaml(cls, _: Any, node: Any) -> InterpolatedReference:
        # TODO: Should we actually have a way to parse this from yaml?
        return cls.parse_dotted(node.value)

register_yaml_class(InterpolatedReference)

class ComplexInterpolatedReference:
    def __init__(self, parts, skip_validation: bool = False) -> None:
        self._parts = parts
        
    def __str__(self) -> str:
        str_components = []
        for part in self._parts:
            if type(part) is InterpolatedReference:
                str_components.append(str(part))
            else:
                str_components.append(part)
        return "".join(str_components)

    @classmethod
    def _splitter(cls, rawstring: str) -> Any:
        if not rawstring:
            return []  # special case - empty string
        interpolatedcomponents = re.findall(r'(\${[a-z][a-z0-9_\.]*[a-z0-9]?}):?',rawstring)
        if not interpolatedcomponents:
            return [rawstring] # special case - no interpolated components     
        remainingstring = rawstring
        components = []
        parts = []
        for ic in interpolatedcomponents:
            parts = remainingstring.split(ic,1)
            if parts[0]:
                components.append(parts[0])
            components.append(ic)
            if parts[1]:
                remainingstring = parts[1]
        if (len(parts) == 2) and (parts[1]):
            components.append(parts[1])
        return components
            

    @classmethod
    def parse(cls, raw: str) -> ComplexInterpolatedReference:
        components = cls._splitter(raw)
        parts = []
        for component in components:
            if component.startswith("$"):
                match = _INTERPOLATION_REGEX.fullmatch(component)
                if not match:
                    raise ReferenceParseError("`component` not a valid interpolated sub-string in `raw`")
                else:
                    parts.append(InterpolatedReference.parse_dotted(match[1]))
            else:
                match = _LITERAL_REGEX.fullmatch(component)
                if not match:
                    raise ReferenceParseError("`component` not a valid sub-string in `raw`")
                else:
                    parts.append(component)
        return cls(parts)




