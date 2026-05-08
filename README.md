# velatus

velatus is a Python library written in Rust for fast log masking and filtering of secrets.

It helps when you have a long list of secrets, and a simple string replace loop starts to get expensive.

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

velatus ships a `SecretFormatter` implemented in Rust with PyO3. It wraps an existing `logging.Formatter`, so handlers keep their normal logging format while the final text gets redacted.

The formatter compiles the secret strings into an Aho-Corasick matcher. Each formatted log message is scanned once, even when you have many secrets.

Matching uses leftmost-longest semantics. If both `abc` and `abcd` are configured as secrets, `abcd` is masked as one complete match even if `abc` appears first in the input list.

By default, velatus replaces matches with `[MASKED]`. You can pass a custom `mask` to `SecretFormatter`, `mask_handlers`, or `mask_exceptions`; velatus treats it as literal text.

Empty secret lists and empty string secrets are rejected with `ValueError`.

To mask secrets in uncaught exceptions too, call `velatus.mask_exceptions(secrets)` after installing the handler formatter. This replaces `sys.excepthook`, formats the traceback, redacts it, and writes the redacted traceback to stderr.
