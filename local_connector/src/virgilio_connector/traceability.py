"""Local-only audit, filtering, conflict detection and central-event export."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing
import uuid


REGISTRO_COLUMNS = (
    "registro_id", "timestamp_utc", "ingresso", "fase", "oggetto",
    "esito", "nota", "correlazioni_tecniche",
)


def global_fingerprint(account_alias: str, message_id: str, message_uid: str,
                       attachment_id: str, sha256: str) -> str:
    source = message_id.strip() or message_uid.strip()
    raw = "\x1f".join((account_alias, source, attachment_id, sha256))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_machine_id(local_root: Path) -> str:
    path = local_root / "machine_id"
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    local_root.mkdir(parents=True, exist_ok=True)
    value = f"caronte-{uuid.uuid4().hex}"
    path.write_text(value + "\n", encoding="utf-8")
    return value


@dataclass(frozen=True, slots=True)
class ImapRule:
    name: str
    action: str
    subject_contains: tuple[str, ...] = ()
    from_contains: tuple[str, ...] = ()
    filename_contains: tuple[str, ...] = ()
    filename_extensions: tuple[str, ...] = ()
    min_attachment_size_bytes: int | None = None
    max_attachment_size_bytes: int | None = None
    require_attachment: bool | None = None

    def matches(self, *, subject: str, sender: str, filename: str | None,
                size_bytes: int, has_attachment: bool = True) -> bool:
        values = (subject.lower(), sender.lower(), (filename or "").lower())
        checks = []
        if self.subject_contains:
            checks.append(any(v.lower() in values[0] for v in self.subject_contains))
        if self.from_contains:
            checks.append(any(v.lower() in values[1] for v in self.from_contains))
        if self.filename_contains:
            checks.append(any(v.lower() in values[2] for v in self.filename_contains))
        if self.filename_extensions:
            checks.append(any(values[2].endswith(v.lower()) for v in self.filename_extensions))
        if self.min_attachment_size_bytes is not None:
            checks.append(size_bytes >= self.min_attachment_size_bytes)
        if self.max_attachment_size_bytes is not None:
            checks.append(size_bytes <= self.max_attachment_size_bytes)
        if self.require_attachment is not None:
            checks.append(has_attachment is self.require_attachment)
        return bool(checks) and all(checks)


@dataclass(frozen=True, slots=True)
class RuleSet:
    default_action: str = "include"
    rules: tuple[ImapRule, ...] = ()

    def decide(self, **values) -> tuple[bool, str | None, str]:
        for rule in self.rules:
            if rule.matches(**values):
                return rule.action == "include", rule.name, f"matched {rule.action} rule"
        included = self.default_action == "include"
        return included, None, f"default_action={self.default_action}"


def load_rules(path: Path) -> RuleSet:
    """Parse the documented rules subset without adding a YAML dependency."""
    lines = path.read_text(encoding="utf-8").splitlines()
    default = "include"
    rules: list[ImapRule] = []
    section = None
    current: dict[str, object] | None = None
    for raw in lines:
        text = raw.split("#", 1)[0].strip()
        if not text:
            continue
        if text == "rules:":
            section = "rules"; continue
        if section != "rules":
            continue
        if text.startswith("default_action:"):
            default = text.split(":", 1)[1].strip()
            continue
        if text in {"include:", "exclude:"}:
            if current:
                rules.append(_make_rule(current))
            current = {"action": text[:-1]}
            continue
        if text.startswith("- name:"):
            if current and "name" in current:
                action = current["action"]
                rules.append(_make_rule(current))
                current = {"action": action}
            if current is not None:
                current["name"] = text.split(":", 1)[1].strip()
            continue
        if current is not None and ":" in text:
            key, value = (part.strip() for part in text.split(":", 1))
            current[key] = _rule_value(value)
    if current and "name" in current:
        rules.append(_make_rule(current))
    if default not in {"include", "exclude"}:
        raise ValueError("rules.default_action must be include or exclude")
    return RuleSet(default, tuple(rules))


def _rule_value(value: str):
    if value.startswith("[") and value.endswith("]"):
        return tuple(item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip())
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return int(value) if value.isdigit() else value.strip("'\"")


def _make_rule(raw: dict[str, object]) -> ImapRule:
    return ImapRule(name=str(raw.get("name", "unnamed")), action=str(raw["action"]),
        subject_contains=tuple(raw.get("subject_contains", ())),
        from_contains=tuple(raw.get("from_contains", ())),
        filename_contains=tuple(raw.get("filename_contains", ())),
        filename_extensions=tuple(raw.get("filename_extensions", ())),
        min_attachment_size_bytes=raw.get("min_attachment_size_bytes"),
        max_attachment_size_bytes=raw.get("max_attachment_size_bytes"),
        require_attachment=raw.get("require_attachment"))


def audit_entry(machine_id: str, action: str, status: str, account_alias: str,
                entity_type: str, entity_id: str, details: dict | None = None) -> dict:
    return {"ts": datetime.now(timezone.utc).isoformat(), "actor": "caronte_locale",
            "machine_id": machine_id, "action": action, "status": status,
            "account_alias": account_alias, "entity_type": entity_type,
            "entity_id": entity_id, "details": details or {}}


class LocalConflictChecker:
    def __init__(self, state_db: Path): self.state_db = state_db

    def check(self) -> dict:
        from .readonly_state import ensure_state_db
        ensure_state_db(self.state_db.parent)
        conflicts, duplicates = [], []
        with closing(sqlite3.connect(self.state_db)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM attachments ORDER BY id").fetchall()
        def grouped(key):
            result = {}
            for row in rows:
                value = key(row)
                if value: result.setdefault(value, []).append(row)
            return result
        for fp, group in grouped(lambda r: r["fingerprint"]).items():
            if len(group) > 1:
                (duplicates if len({r["sha256"] for r in group}) == 1 else conflicts).append(
                    {"type": "duplicate_seen" if len({r['sha256'] for r in group}) == 1 else "conflict_hash_mismatch", "fingerprint": fp})
        for identity, group in grouped(lambda r: (r["account_alias"], r["attachment_id"]) if r["attachment_id"] else None).items():
            if len(group) > 1 and len({r["sha256"] for r in group}) > 1:
                conflicts.append({"type": "conflict_hash_mismatch", "attachment_id": identity[1]})
        for name, group in grouped(lambda r: r["staged_filename"]).items():
            if len(group) > 1 and len({r["sha256"] for r in group}) > 1:
                conflicts.append({"type": "conflict_filename_collision", "staged_filename": name})
        for name, group in grouped(lambda r: r["manifest_path"]).items():
            if len({r["attachment_id"] for r in group}) > 1:
                conflicts.append({"type": "conflict_manifest_collision", "manifest_path": name})
        return {"status": "CONFLICTS" if conflicts else "WARNINGS" if duplicates else "OK",
                "conflicts": conflicts, "duplicates": duplicates}


def export_central_events(state_db: Path, local_root: Path, format_name: str) -> Path:
    rows = central_event_rows(state_db)

    out = local_root / "exports"; out.mkdir(parents=True, exist_ok=True)
    target = out / f"central_events_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.{format_name}"
    if format_name == "jsonl":
        target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    elif format_name == "csv":
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["event_id"]); writer.writeheader(); writer.writerows(rows)
    else:
        raise ValueError("format must be jsonl or csv")
    return target


def export_registro_events(state_db: Path, local_root: Path, format_name: str) -> Path:
    rows = registro_event_rows(state_db)

    out = local_root / "exports"; out.mkdir(parents=True, exist_ok=True)
    target = out / f"registro_events_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.{format_name}"
    if format_name == "jsonl":
        target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    elif format_name == "csv":
        with target.open("w", encoding="utf-8", newline="") as stream:
            columns = list(rows[0]) if rows else list(REGISTRO_COLUMNS)
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    else:
        raise ValueError("format must be jsonl or csv")
    return target


def central_event_rows(state_db: Path) -> list[dict]:
    """Build export rows in memory without modifying SQLite or local files.

    Legacy attachment rows missing attachment_id/sha256 are intentionally skipped.
    """
    from .readonly_state import ensure_state_db
    ensure_state_db(state_db.parent)
    with closing(sqlite3.connect(state_db)) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute("""SELECT e.id,e.created_at,e.machine_id,e.account_alias,
            e.entity_id AS attachment_id,e.fingerprint,e.action AS event_type,e.status AS result,
            e.details_json,a.source_email,a.sha256,a.status AS local_state,a.staged_filename,
            a.staged_path,a.manifest_path,m.message_id AS source_message_id,m.message_uid AS source_message_uid
            FROM audit_events e LEFT JOIN attachments a ON a.attachment_id=e.entity_id
            LEFT JOIN messages m ON m.id=a.message_id
            WHERE e.fingerprint IS NOT NULL AND e.fingerprint != ''
              AND NOT EXISTS (
                    SELECT 1 FROM attachments legacy
                    WHERE legacy.account_alias=e.account_alias
                      AND legacy.fingerprint=e.fingerprint
                      AND (legacy.attachment_id IS NULL OR legacy.sha256 IS NULL)
                )
            ORDER BY e.id""")]
    for row in rows:
        row["event_id"] = hashlib.sha256(f"{row['machine_id']}|{row['event_type']}|{row['fingerprint']}|{row['created_at']}".encode()).hexdigest()
        row["global_state_suggestion"] = _global_state(row["event_type"], row["local_state"])
        row["conflict_type"] = row["event_type"] if str(row["event_type"]).startswith("conflict_") else ""
        row["notes"] = row.pop("details_json") or ""
    rows.sort(key=lambda row: (
        str(row.get("created_at", "")),
        str(row.get("fingerprint", "")),
        str(row.get("machine_id", "")),
        str(row.get("event_type", "")),
        str(row.get("attachment_id", "")),
        str(row.get("event_id", "")),
    ))
    return rows


def registro_event_rows(state_db: Path) -> list[dict]:
    return [_registro_row(row) for row in central_event_rows(state_db)]


def _registro_row(row: dict) -> dict:
    return {
        "registro_id": row["event_id"],
        "timestamp_utc": row.get("created_at", ""),
        "ingresso": "Local connector",
        "fase": _registro_phase(row),
        "oggetto": _registro_object(row),
        "esito": _registro_outcome(row),
        "nota": _registro_note(row),
        "correlazioni_tecniche": _registro_correlations(row),
    }


def _registro_phase(row: dict) -> str:
    action = str(row.get("event_type", "") or "").strip()
    local_state = str(row.get("local_state", "") or "").strip()
    conflict_type = str(row.get("conflict_type", "") or "").strip()
    if conflict_type or action.startswith("conflict_"):
        return "conflitto"
    if action == "message_completed":
        return "pratica finale"
    if action == "da_archiviare_intake":
        return "da archiviare"
    if action == "attachment_staged" or local_state == "staged_storage":
        return "limbo"
    if action == "failed":
        return "errore"
    return "acquisizione"


def _registro_object(row: dict) -> str:
    for key in ("attachment_id", "source_message_id", "source_message_uid", "fingerprint"):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return str(row.get("machine_id", "") or "").strip()


def _registro_outcome(row: dict) -> str:
    action = str(row.get("event_type", "") or "").strip()
    result = str(row.get("result", "") or "").strip()
    conflict_type = str(row.get("conflict_type", "") or "").strip()
    if conflict_type or action.startswith("conflict_"):
        return "conflitto"
    if action == "da_archiviare_intake":
        return "errore" if result == "failed" else "attesa_umano"
    if action == "failed" or result == "failed":
        return "errore"
    if action == "message_completed" or result == "completed":
        return "archiviato"
    if action in {"duplicate_seen", "skipped"} or result in {"duplicate_seen", "skipped"}:
        return "attesa_umano"
    return "ok"


def _registro_note(row: dict) -> str:
    action = str(row.get("event_type", "") or "evento").replace("_", " ").strip()
    object_id = str(row.get("attachment_id", "") or "").strip()
    if object_id:
        action = f"{action} {object_id}"
    result = str(row.get("result", "") or "").strip()
    if result:
        action = f"{action} -> {result}"
    return action


def _registro_correlations(row: dict) -> str:
    payload = {}
    for key in (
        "machine_id", "account_alias", "source_email", "source_message_id",
        "source_message_uid", "attachment_id", "fingerprint", "sha256",
        "event_type", "result", "local_state", "staged_filename", "staged_path",
        "manifest_path",
    ):
        value = row.get(key, "")
        if value not in {"", None}:
            payload[key] = value
    details = str(row.get("notes", "") or "").strip()
    if details:
        payload["details"] = details
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _global_state(action, state):
    if str(action).startswith("conflict_"): return "conflict"
    if action == "duplicate_seen": return "duplicate_seen"
    if action in {"failed"}: return "failed"
    if action == "skipped": return "skipped"
    if action == "message_completed": return "completed"
    if state == "staged_storage": return "staged"
    return "acquired"
