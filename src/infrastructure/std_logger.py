import logging

from ..application.ports.logger import Logger


class StdLogger(Logger):
    def __init__(self, name: str = "ai-chat") -> None:
        self._logger = logging.getLogger(name)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def error(self, message: str) -> None:
        self._logger.error(message)
