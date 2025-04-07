from typing import Optional
from .velatus import *

import logging

__doc__ = velatus.__doc__


def mask_handlers(secrets: list[str], handlers: list[logging.Handler], mask: Optional[str] = None) -> None:
    """Install a Masker as a filter on all given handlers."""
    # Create a Masker instance
    masker = Masker(secrets, mask=mask)

    # Iterate through all handlers
    for handler in handlers:
        handler.addFilter(masker)


__all__ = ["Masker"]