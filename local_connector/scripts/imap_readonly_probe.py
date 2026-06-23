"""Controlled LC3 probe: dry-run or local quarantine, never mailbox mutation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from virgilio_connector.imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.readonly_quarantine import ReadonlyQuarantineRunner
from virgilio_connector.scanner import select_scanner


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise SystemExit(f"missing environment variable: {name}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Virgilio read-only IMAP probe")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="list decisions; write nothing")
    mode.add_argument("--download", action="store_true", help="save allowed attachments locally")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    load_env_file(args.env_file)
    config = ImapReadonlyConfig(
        host=required("VIRGILIO_IMAP_HOST"),
        port=int(os.environ.get("VIRGILIO_IMAP_PORT", "993")),
        username=required("VIRGILIO_IMAP_USERNAME"),
        password=required("VIRGILIO_IMAP_PASSWORD"),
        mailbox=os.environ.get("VIRGILIO_IMAP_MAILBOX", "Virgilio/da-traghettare"),
        max_messages=int(os.environ.get("VIRGILIO_IMAP_MAX_MESSAGES", "10")),
    )
    paths = LocalDataPaths(Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data")))
    runner = ReadonlyQuarantineRunner(
        mailbox=ImapReadonlyMailbox(config, paths.incoming), paths=paths,
        max_attachment_bytes=int(os.environ.get("VIRGILIO_MAX_ATTACHMENT_BYTES", str(25 * 1024 * 1024))),
        scanner=select_scanner(os.environ.get("VIRGILIO_SCANNER", "auto")))
    items = runner.run(dry_run=args.dry_run)
    print(f"mode={'dry-run' if args.dry_run else 'download'} attachments={len(items)}")
    for item in items:
        print(f"uid={item.message_uid} ordinal={item.ordinal} decision={item.decision} "
              f"size={item.size_bytes} saved={str(item.saved).lower()}")


if __name__ == "__main__":
    main()
