"""Benchmark tests for the Velatus library"""

import logging

import pytest
import velatus
from pytest_benchmark.fixture import BenchmarkFixture

MANY_MESSAGES = 100000

log = logging.getLogger(__name__)


@pytest.fixture
def secret_env() -> list[str]:
    """Fixture to provide a list of secrets"""
    secrets = [
        "my_secret_key",
        "my_password",
        "my_token",
        "line1",
        "line2",
        "line3",
    ]
    secrets.extend(
        [
            f"xxx{i}"
            for i in range(1, 41)
        ]
    )
    return secrets


# Create a logging handler that formats but doesn't log
class QuietHandler(logging.Handler):
    """A logging handler that formats but doesn't log"""

    def __init__(self) -> None:
        """Initialize the handler"""
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """Format the log record but don't print it"""
        self.format(record)


def string_secret_filtering(
    secret_env: list[str],
    handlers: list[logging.Handler],
) -> None:
    """Configure string secrets filtering for the given handlers"""
    log.info("Masking for %d secrets", len(secret_env))

    def _filter_secrets(s: logging.LogRecord) -> bool:
        for secret in secret_env:
            s.msg = str(s.msg).replace(secret, "[MASKED]")
        return True

    # Mask any secrets from environment variables
    for handler in handlers:
        handler.addFilter(_filter_secrets)


def log_many_messages(logger: logging.Logger) -> None:
    """Log many messages with secrets"""
    for i in range(MANY_MESSAGES):
        logger.debug("Logging message with secret: my_secret_key %d", i)
        logger.debug("Logging message without any secrets")


# Benchmark the string_secret_filtering function
# by logging lots of messages with secrets and getting the time taken
@pytest.mark.benchmark(
    warmup=True,
)
def test_benchmark_string_secret_filtering(
    benchmark: BenchmarkFixture,
    secret_env: list[str],
) -> None:
    """Test the string_secret_filtering function"""
    # Create a logger
    logger = logging.getLogger("test_benchmark_string_secret_filtering")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    handler = QuietHandler()
    logger.addHandler(handler)

    # Configure string secret filtering
    string_secret_filtering(secret_env, [handler])

    # Benchmark the logging of messages
    benchmark(
        log_many_messages,
        logger,
    )


# Benchmark the Velatus mask_handlers function
# by logging lots of messages with secrets and getting the time taken
@pytest.mark.benchmark(
    warmup=True,
)
def test_benchmark_mask_handlers(
    secret_env: list[str],
    benchmark: BenchmarkFixture,
) -> None:
    """Test the mask_handlers function"""
    # Create a logger
    logger = logging.getLogger("test_benchmark_mask_handlers")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    handler = QuietHandler()
    logger.addHandler(handler)

    # Configure the secret filtering
    velatus.mask_handlers(secret_env, [handler])

    # Benchmark the logging of messages
    benchmark(
        log_many_messages,
        logger,
    )


# Benchmark the base functionality
# with no filtering at all.
@pytest.mark.benchmark(
    warmup=True,
)
def test_benchmark_no_filtering(
    benchmark: BenchmarkFixture,
) -> None:
    """Test the base function"""
    # Create a logger
    logger = logging.getLogger("test_benchmark_no_filtering")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    handler = QuietHandler()
    logger.addHandler(handler)

    # Benchmark the logging of messages
    benchmark(
        log_many_messages,
        logger,
    )
