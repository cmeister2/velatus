import logging

class Masker:
    """A class to mask sensitive information in log records."""

    def __init__(self, strings: list[str], mask: str | None = None) -> None: ...

    def __call__(self, log_record: logging.LogRecord) -> bool: ...
