from typing import Any, Callable, Iterable, Optional, Union

from opta.exceptions import UserErrors

DEFAULT_VERSION = 1
CURRENT_VERSION = 2

Handler = Callable[[dict], None]


class VersionProcessor:
    """
    Processes a layer YAML for specific versions.
    """
    def __init__(
        self,
        *,
        versions: Union[int, Iterable[int]],
        next_version: Optional[int] = None,
        handlers: Iterable[Handler] = tuple(),
    ):
        """
        `versions` is a single YAML version or an iterable of different versions.
        `next_version` is the version that this processor converts to;
            if unspecified and only a single version is given to `versions`, this defaults to the version plus one.
        `handlers` is the list of callables that will do the processing from one version to another
        """
        if isinstance(versions, int):
            versions = (versions,)

        self.versions = tuple(versions)

        if next_version is None:
            if len(self.versions) > 1:
                raise ValueError(
                    f"must supply next_version when a {type(self).__name__} supports multiple versions"
                )

            next_version = self.versions[0] + 1

        self.next_version = next_version
        self.handlers = tuple(handlers)

    def process(self, data: dict) -> None:
        for handler in self.handlers:
            handler(data)

        data["version"] = self.next_version


class ModuleHandler:
    """
    A `Handler` that handles each module in the YAML separately.
    It can either be used by subclassing and overriding the `run` method, or passing the `handler` parameter in the constructor.
    """
    def __init__(self, handler: Optional[Handler] = None):
        """
        `handler` is the Handler that is called for each module this `ModuleHandler` processes.
        If not passed, this class must be subclasses instead and the `run` method overridden.
        """
        self._handler = handler

        # Validate invariants now to "fail fast" instead of waiting for the handler to actually be used
        if not self._handler:
            parent = ModuleHandler
            child = self.__class__
            if parent.run == child.run and parent.__call__ == child.__call__:
                # No handler passed, and subclass hasn't overridden the `run` or __call__ methods.
                raise RuntimeError("Must pass a handler if not using a child class that overrides run or __call__")



    def __call__(self, data: dict) -> None:
        """

        """
        modules = data.get("modules", [])
        if not isinstance(modules, list):
            raise UserErrors("Expected `modules` in layer to be list")

        for idx, module in enumerate(modules):
            if not isinstance(module, dict):
                raise UserErrors(f"Expected `modules[{idx}]` to be dict")

            if not self.should_handle(module):
                continue

            self.run(module)

    def should_handle(self, module: dict) -> bool:
        return True

    def run(self, module: dict) -> None:
        if self._handler:
            self._handler(module)
        else:
            raise NotImplementedError("Child class must implement this method")


class ModuleTypeHandler(ModuleHandler):
    def __init__(self, types: Union[str, Iterable[str]], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if isinstance(types, str):
            types = (types,)

        self.__types = tuple(types)

    def should_handle(self, module: dict) -> bool:
        try:
            type = module["type"]
        except KeyError:
            raise UserErrors("Module type not set")

        return type in self.__types
