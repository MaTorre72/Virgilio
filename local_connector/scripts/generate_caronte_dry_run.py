"""Generate local Caronte JSON artifacts; performs no network calls."""

from __future__ import annotations

import os
from pathlib import Path

from virgilio_connector.caronte_dry_run import (
    CaronteDryRunConfig,
    generate_caronte_dry_run_files,
)

from imap_readonly_probe import load_env_file


def main() -> None:
    load_env_file(Path(".env"))
    root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
    config = CaronteDryRunConfig(
        connector_id=os.environ.get("VIRGILIO_CONNECTOR_ID", "local-readonly-probe"),
        account_alias=os.environ.get("VIRGILIO_ACCOUNT_ALIAS", "gmail-test"),
        provider_hint=os.environ.get("VIRGILIO_PROVIDER_HINT", "gmail_imap"),
    )
    files = generate_caronte_dry_run_files(
        root / "state.db", root / "commands" / "dry-run", config=config)
    print(f"caronte_dry_run_files={len(files)}")
    for path in files:
        print(path.name)


if __name__ == "__main__":
    main()
