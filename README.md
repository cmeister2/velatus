# velatus

velatus is a Python library written in Rust for fast log masking/filtering of secrets.

It is useful when you have a lot of secrets to match, when a simple string-replace may not be performant.

## Basic usage

```python
import logging
import sys
import velatus

def main():
    secrets = ["secret1", "secret2"]
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    velatus.mask_handlers(secrets, logging.getLogger().handlers)

    logging.info("Printing out secret1, secret2")

if __name__ == "__main__":
    main()
```
gives
```
INFO:root:Printing out [MASKED], [MASKED]
```

## Design

velatus ships a `SecretFormatter` implemented in Rust with pyo3. It wraps any existing `logging.Formatter`, so you can attach it to handlers via `setFormatter` without losing their formatting configuration.

Under the covers, the `SecretFormatter` compiles the set of strings into a single regular expression using the `regex` crate, then substitutes every match with `[MASKED]` (or a custom replacement if you provide one).

To mask secrets in uncaught exceptions as well, call `velatus.mask_exceptions(secrets)` after installing the handler formatter. This replaces `sys.excepthook` so tracebacks written to stderr are redacted before they reach the console or logs.
