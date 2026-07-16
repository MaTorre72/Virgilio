"""Executable entry point for the standalone Caronte distribution."""

from __future__ import annotations

import sys


def main() -> int:
    """Open Caronte, while retaining internal commands for owned workers."""

    if len(sys.argv) > 1:
        from virgilio_connector.__main__ import main as command_main

        result = command_main()
        return int(result or 0)

    from virgilio_connector.user_app import launch_user_app

    return launch_user_app()


if __name__ == "__main__":
    raise SystemExit(main())
