"""Tests for the SecretFormatter implementation."""

import io
import logging
import sys
from typing import Any

import pytest
import velatus

log = logging.getLogger(__name__)


def make_log_record(msg: Any) -> logging.LogRecord:
    """Create a LogRecord with the given message."""
    return logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )


def test_secret_formatter_masks_message() -> None:
    """SecretFormatter should redact configured secrets."""
    formatter = velatus.SecretFormatter(
        secrets=["xxx", "yyy"],
        existing_formatter=logging.Formatter("%(message)s"),
    )

    record = make_log_record("This is a log message with secret xxx and yyy")
    masked = formatter.format(record)

    assert masked == "This is a log message with secret [MASKED] and [MASKED]"


def test_secret_formatter_custom_mask() -> None:
    """SecretFormatter should support a constant replacement mask."""
    formatter = velatus.SecretFormatter(
        secrets=["xxx"],
        mask="[REDACTED]",
        existing_formatter=logging.Formatter("%(message)s"),
    )

    record = make_log_record("Secret value xxx present")
    masked = formatter.format(record)
    assert masked == "Secret value [REDACTED] present"


def test_secret_formatter_bytes_message() -> None:
    """SecretFormatter should handle byte messages."""
    formatter = velatus.SecretFormatter(
        secrets=["xxx"],
        existing_formatter=logging.Formatter("%(message)s"),
    )

    record = make_log_record(b"Secret value xxx present")
    masked = formatter.format(record)
    # The underlying formatter converts the bytes to a string with the b'' prefix
    assert masked == "b'Secret value [MASKED] present'"


def test_secret_formatter_weird_object() -> None:
    """SecretFormatter should handle arbitrary objects."""

    class WeirdObject:
        def __str__(self) -> str:
            return "Weird object with xxx"

    formatter = velatus.SecretFormatter(
        secrets=["xxx"],
        existing_formatter=logging.Formatter("%(message)s"),
    )

    record = make_log_record(WeirdObject())
    masked = formatter.format(record)
    assert masked == "Weird object with [MASKED]"


def test_secret_formatter_requires_secret() -> None:
    """SecretFormatter should raise when no secrets are provided."""
    with pytest.raises(ValueError):
        velatus.SecretFormatter(secrets=[])


def test_mask_handlers_installs_formatter() -> None:
    """mask_handlers should wrap handlers with SecretFormatter."""
    handler = logging.StreamHandler(io.StringIO())

    velatus.mask_handlers(["xxx"], [handler])

    assert isinstance(handler.formatter, velatus.SecretFormatter)

    record = make_log_record("Contains xxx value")
    formatted = handler.format(record)
    assert formatted == "Contains [MASKED] value"


def test_mask_handlers_requires_secrets() -> None:
    """mask_handlers should reject empty secret lists."""
    with pytest.raises(ValueError):
        velatus.mask_handlers([], [])


def test_mask_exceptions_masks_sys_excepthook() -> None:
    """mask_exceptions should redact secrets written by sys.excepthook."""
    original_hook = sys.excepthook
    original_stderr = sys.stderr

    try:
        velatus.mask_exceptions(["supersecret"])

        buffer = io.StringIO()
        sys.stderr = buffer

        sys.excepthook(ValueError, ValueError("supersecret"), None)

        output = buffer.getvalue()
        assert "[MASKED]" in output
        assert "supersecret" not in output
    finally:
        sys.stderr = original_stderr
        sys.excepthook = original_hook
