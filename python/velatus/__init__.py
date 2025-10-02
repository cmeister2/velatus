"""Velatus: A Python library for masking sensitive information in logs."""

import logging
import sys
from typing import Optional

from .velatus import SecretFormatter

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def mask_handlers(
    secrets: list[str], handlers: list[logging.Handler], mask: Optional[str] = None
) -> None:
    """Install a SecretFormatter on all given handlers."""
    if not secrets:
        raise ValueError("At least one secret must be provided")

    for handler in handlers:
        existing_formatter = handler.formatter
        formatter = SecretFormatter(
            secrets=secrets,
            mask=mask,
            existing_formatter=existing_formatter,
        )
        handler.setFormatter(formatter)

def mask_exceptions(secrets: list[str], mask: Optional[str] = None) -> None:
    """Install a SecretFormatter as sys.excepthook."""
    if not secrets:
        raise ValueError("At least one secret must be provided")
    exc_formatter = SecretFormatter(secrets=secrets, mask=mask)
    sys.excepthook = exc_formatter.handle_exception



__all__ = [
    "SecretFormatter",
    "mask_handlers",
    "mask_exceptions",
    "__doc__",
]
