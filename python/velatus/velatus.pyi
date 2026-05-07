import logging
from types import TracebackType

class SecretFormatter(logging.Formatter):
    """Formatter that masks sensitive information in log messages."""

    def __init__(
        self,
        secrets: list[str],
        mask: str | None = None,
        existing_formatter: logging.Formatter | None = None,
    ) -> None: ...
    def format(self, record: logging.LogRecord) -> str: ...
    def handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None: ...
