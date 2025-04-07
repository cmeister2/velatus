"""Velatus: A Python library for masking sensitive information in logs."""

import logging
from typing import Optional

from .velatus import Masker


def mask_handlers(
    secrets: list[str], handlers: list[logging.Handler], mask: Optional[str] = None
) -> None:
    """Install a Masker as a filter on all given handlers."""
    # Create a Masker instance
    masker = Masker(secrets, mask=mask)

    # Iterate through all handlers
    for handler in handlers:
        handler.addFilter(masker)


__all__ = ["Masker", "mask_handlers", "__doc__"]
