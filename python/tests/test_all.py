"""Test the Masker class with different parameters."""

import logging
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


@pytest.mark.parametrize(
    "mask, strings_to_mask, log_record, expected",
    [
        (
            None,
            ["xxx", "yyy"],
            "This is a log message with secret xxx and yyy",
            "This is a log message with secret [MASKED] and [MASKED]",
        ),
        (
            "[REDACTED]",
            ["xxx", "yyy"],
            "This is a log message with secret xxx and yyy",
            "This is a log message with secret [REDACTED] and [REDACTED]",
        ),
        (
            None,
            ["$TEST"],
            "This is a test message with $TEST",
            "This is a test message with [MASKED]",
        ),
        (
            None,
            ["[A-Z]"],
            "This [A-Z] is a test message with [A-Z]",
            "This [MASKED] is a test message with [MASKED]",
        ),
        (
            None,
            ["\\"],
            "This is a test message with \\ and \\",
            "This is a test message with [MASKED] and [MASKED]",
        ),
        (
            None,
            ["xyz"],
            "This is a test message without a secret",
            "This is a test message without a secret",
        )
    ],
)
def test_masker(mask, strings_to_mask, log_record, expected):
    """Test the Masker class with different parameters."""
    m = velatus.Masker(strings_to_mask, mask=mask)

    # Use the masker to mask the log record
    llr = make_log_record(log_record)

    log.info(f"Original log record: {llr.msg}")
    m(llr)
    log.info(f"Masked log record: {llr.msg}")

    # Check if the log record message is masked
    assert llr.msg == expected


def test_empty_list() -> None:
    """Test the Masker with an empty list."""
    with pytest.raises(ValueError):
        velatus.Masker([])

def test_bytes() -> None:
    """Test that the Masker can handle bytes in the LogRecord."""
    m = velatus.Masker(["xxx", "yyy"])
    llr = make_log_record(b"This is a log message with secret xxx and yyy")
    m(llr)
    assert llr.msg == "This is a log message with secret [MASKED] and [MASKED]"

def test_weird_record() -> None:
    """Test that the Masker can handle objects in the LogRecord."""
    m = velatus.Masker(["xxx", "yyy"])

    class WeirdObject:
        """A weird object for testing purposes."""

        def __str__(self) -> str:
            """Return a string representation of the object."""
            return "This is a weird object with secret xxx and yyy"

    llr = make_log_record(WeirdObject())
    m(llr)
    assert llr.msg == "This is a weird object with secret [MASKED] and [MASKED]"
