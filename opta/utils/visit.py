# new-module-api

from collections.abc import Iterable, MutableMapping, MutableSequence
from typing import Any, Callable, Iterator, List, Optional, Tuple, Union

from opta.utils.ref import PathElement, Reference

Filter = Callable[[Any], bool]
Builder = Callable[[Any], List[PathElement]]
MutableCollection = Union[MutableSequence, MutableMapping]


class Visitor:
    def __init__(
        self,
        root: Iterable,
        *,
        depth_first: bool = True,
        filter: Optional[Filter] = None,
        builder: Optional[Builder] = None,
    ):
        self._root = root
        self.depth_first = depth_first
        self.filter: Filter = filter or (lambda _: True)
        self.builder: Builder = builder or visit_list_or_dict

    @property
    def root(self) -> Iterable:
        return self._root

    def __contains__(self, path: Any) -> bool:
        if not isinstance(path, Reference):
            raise TypeError(f"path must be of type {Reference.__qualname__}")

        current: Any = self.root
        for part in path:
            try:
                next = current[part]
            except (TypeError, KeyError, IndexError):
                return False

            current = next

        return True

    def __iter__(self) -> Iterator[Tuple[Reference, Any]]:
        iter = _VisitorIterator(self)
        iter.depth_first = self.depth_first
        iter.filter = self.filter
        iter.builder = self.builder
        return iter

    def __getitem__(self, path: Any) -> Any:
        if not isinstance(path, Reference):
            raise TypeError(f"index must be of type {Reference.__qualname__}")

        current: Any = self.root
        for part in path:
            current = current[part]

        return current

    def __setitem__(self, path: Reference, value: Any) -> None:
        self.set(path, value)

    def set(
        self,
        path: Reference,
        value: Any,
        *,
        allow_missing_leaf: Optional[bool] = None,
        fill_missing: Optional[Callable[[Reference], MutableCollection]] = None,
    ) -> None:
        current: Any = self.root
        total = len(path)
        # TODO: Should leave root unmodified if there is an error before value is set
        for idx, part in enumerate(path):
            # Check if this is the last piece of the path
            if idx + 1 == total:
                break

            try:
                next = current[part]
            except KeyError:
                if not fill_missing:
                    raise

                current_ref = path[0 : idx + 1]
                next = fill_missing(current_ref)
                current[part] = next

            current = next

        if part not in current:
            if allow_missing_leaf is False or not fill_missing:
                raise IndexError("cannot add new value")

        current[part] = value


class _VisitorIterator:
    def __init__(self, visitor: Visitor) -> None:
        self.visitor = visitor
        self.to_visit: List[Reference] = []
        self.filter: Filter = lambda _: True
        self.builder: Builder = visit_list_or_dict
        self.depth_first: bool = True

        self._populate_to_visit()

    def __iter__(self) -> Iterator[Tuple[Reference, Any]]:
        return self

    def __next__(self) -> Tuple[Reference, Any]:
        while self.to_visit:
            ref = self._pop_next_ref()
            value = self.visitor[ref]

            if not self.filter(value):
                continue

            self._add_children(ref, value)
            return ref, value

        raise StopIteration

    def _pop_next_ref(self) -> Reference:
        if self.depth_first:
            return self.to_visit.pop()
        else:
            return self.to_visit.pop(0)

    def _populate_to_visit(self) -> None:
        """Sets up initial to_visit list"""

        self._add_children(Reference(), self.visitor.root)

    def _add_children(self, parent: Reference, of: Any) -> None:
        children = self.builder(of)
        if self.depth_first:
            # If we are depth first, we want to put the first items last
            children.reverse()

        self.to_visit.extend(parent.child(child) for child in children)


def visit_list_or_dict(obj: Any) -> List[PathElement]:
    indexes: List[PathElement] = []
    if isinstance(obj, dict):
        indexes = list(obj.keys())

    elif isinstance(obj, list):
        indexes = list(range(len(obj)))

    # Filter out non-str or int indexes
    indexes = [idx for idx in indexes if isinstance(idx, str) or isinstance(idx, int)]

    return indexes


def fill_missing_list_or_dict(path: Reference) -> MutableCollection:
    """
    Returns an empty list if the last element of `path` is a an int, otherwise returns an empty dict
    """

    last = path[-1]

    if isinstance(last, int):
        return []

    return {}
