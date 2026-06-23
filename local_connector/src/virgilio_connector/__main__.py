"""Command-line entrypoint for explicit, opt-in connector actions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .caronte_http import CaronteDryRunClientError, CaronteDryRunHttpClient


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    _load_env_file(Path(".env"))
    parser = argparse.ArgumentParser(prog="python -m virgilio_connector")
    commands = parser.add_subparsers(dest="command", required=True)
    sender = commands.add_parser("send-caronte-dry-run")
    sender.add_argument("--command-file", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "send-caronte-dry-run":
        client = CaronteDryRunHttpClient(
            os.environ.get("VIRGILIO_CARONTE_DRY_RUN_URL"),
            timeout_seconds=float(os.environ.get("VIRGILIO_CARONTE_TIMEOUT_SECONDS", "15")),
        )
        try:
            result = client.send_command_file(args.command_file)
        except CaronteDryRunClientError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(
            f"ok={str(result.ok).lower()} dry_run=true "
            f"accepted={result.accepted_attachments} rejected={result.rejected_attachments}"
        )
        return 0 if result.ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
