import pytest
import velatus


class LightLogRecord:
    def __init__(self, msg: str) -> None:
        self.msg = msg


@pytest.mark.parametrize(
    "mask, strings_to_mask, log_record, expected",
    [
        (None, ["xxx", "yyy"], "This is a log message with secret xxx and yyy", "This is a log message with secret [MASKED] and [MASKED]"),
        ("[REDACTED]", ["xxx", "yyy"], "This is a log message with secret xxx and yyy", "This is a log message with secret [REDACTED] and [REDACTED]"),
        (None, ["$TEST"], "This is a test message with $TEST", "This is a test message with [MASKED]"),
        (None, ["[A-Z]"], "This [A-Z] is a test message with [A-Z]", "This [MASKED] is a test message with [MASKED]"),
        (None, ["\\"], "This is a test message with \\ and \\", "This is a test message with [MASKED] and [MASKED]"),
    ]
)
def test_masker(mask, strings_to_mask, log_record, expected):
    """
    Test the Masker class with different parameters.
    """
    m = velatus.Masker(strings_to_mask, mask=mask)

    # Use the masker to mask the log record
    llr = LightLogRecord(log_record)

    print(f"Original log record: {llr.msg}")
    m(llr)
    print(f"Masked log record: {llr.msg}")

    # Check if the log record message is masked
    assert llr.msg == expected
