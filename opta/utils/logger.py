import logging

from colored import attr, fg


class Logger:
    def __init__(self) -> None:
        self.logger = logging.getLogger("opta")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

    def debug(self, msg, *args, **kwargs) -> None:  # type: ignore
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:  # type: ignore
        self.logger.warning(f"{fg('yellow')}{msg}{attr(0)}", *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:  # type: ignore
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs) -> None:  # type: ignore
        self.logger.error(f"{fg('magenta')}{msg}{attr(0)}", *args, **kwargs)

    def exception(self, msg, *args, **kwargs) -> None:  # type: ignore
        self.logger.exception(f"{fg('magenta')}{msg}{attr(0)}", *args, **kwargs)

    def addHandler(self, handler) -> None:  # type: ignore
        self.logger.addHandler(handler)

    def isEnabledFor(self, level) -> bool:  # type: ignore
        return self.logger.isEnabledFor(level)
