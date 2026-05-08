#!/usr/bin/env python3
"""Replace the sentinel version 0.0.0 with the release version."""
import sys

VERSION = sys.argv[1]

for path in ("Cargo.toml", "Cargo.lock"):
    text = open(path).read()
    text = text.replace('version = "0.0.0"', f'version = "{VERSION}"', 1)
    open(path, "w").write(text)
