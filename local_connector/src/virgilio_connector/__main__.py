"""Minimal bootstrap for ``python -m virgilio_connector``."""

from . import cli as _cli

main = _cli.main

if __name__ == "__main__":
    raise SystemExit(main())
