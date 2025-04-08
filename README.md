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

velatus consists of a `Masker` class which is callable and written in Rust using pyo3. It may be installed as a filter on a logging Handler with `addFilter`.

Under the covers, the `Masker` compiles the set of strings to a regular expression using the `regex` library, then substitutes all matches with the configured masking value.
