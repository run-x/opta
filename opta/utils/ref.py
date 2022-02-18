# new-module-api

from __future__ import annotations

import functools
import re
from collections import abc
from typing import (
    Any,
    Iterable,
    Iterator,
    List,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

_PART_STR_REGEX = re.compile(r"(?:[a-z]([a-z0-9_]*[a-z0-9])?)", re.IGNORECASE)


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

        path = ", ".join(repr(part) for part in self._path)

        return f"{cls}({path})"

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
        parts: List[PathElement] = list(
            raw.split(".")
        )  # Wrap in `list()` call to appease type checker

        for idx, part in enumerate(parts[:]):
            try:
                part = int(part)
            except ValueError:
                continue

            parts[idx] = part

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
                if not _PART_STR_REGEX.fullmatch(part):
                    raise ValueError(f"Path part {idx} invalid: {part}")
            else:
                raise TypeError(f"unsupported part type {type(part).__name__}")
