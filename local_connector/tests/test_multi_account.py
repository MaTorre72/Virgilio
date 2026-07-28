from pathlib import Path
from dataclasses import dataclass
import sqlite3
import json
import sys

import pytest

from virgilio_connector.imap_readonly import DetectedAttachment
from virgilio_connector.completion import ControlledAckRunner, LocalCompletionRunner
from virgilio_connector.multi_account import (
    LocalImapAccount,
    MultiAccountScanResult,
    MultiAccountImapProcessor,
    MultiAccountConfigError,
    MultiAccountReadonlyScanner,
    LocalStorageConfig,
    scaffold_local_config,
    load_storage_config,
    load_multi_account_config,
)
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.ports import MessageReference
from virgilio_connector.scanner import LocalScanResult, ScanVerdict
from virgilio_connector.storage_adapter import (
    LocalFilesystemStorageAdapter,
    StorageStageResult,
    StorageAdapterError,
)
from virgilio_connector.bucoliche import (
    BucolicheAppendOnlyAdapter,
    operational_event_rows,
)
from virgilio_connector.pipeline import LocalPipelineRunner
from virgilio_connector.reset_local_state import reset_local_state
from virgilio_connector.operational_handoff import OperationalHandoffResult
from virgilio_connector.doctor import LocalDoctor
from virgilio_connector.traceability import load_rules
from virgilio_connector.attachment_identity import canonical_attachment_id
from virgilio_connector.readonly_state import ReadonlyStateStore


def write_config(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "accounts.yaml"
    path.write_text("""accounts:
  - account_alias: account_1
    email: account.1@example.invalid
    provider_hint: gmail_workspace
    imap_host: imap.gmail.com
    imap_port: 993
    username_env: VIRGILIO_IMAP_ACCOUNT_1_USERNAME
    password_env: VIRGILIO_IMAP_ACCOUNT_1_PASSWORD
    input_folder: Virgilio/da-traghettare
    done_folder: Virgilio/traghettate
    error_folder: Virgilio/errore
    enabled: true
    max_messages: 7
    ack_enabled: true
    ack_strategy: add_done_label_only
  - account_alias: disabled_box
    email: disabled@example.invalid
    provider_hint: generic_imap
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_IMAP_DISABLED_USERNAME
    password_env: VIRGILIO_IMAP_DISABLED_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
    enabled: false
""", encoding="utf-8")
    return path


def write_storage_config(tmp_path: Path, staging_dir: Path, *,
                         use_account_subfolders=True) -> Path:
    path = write_config(tmp_path)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"""
storage:
  adapter: local_filesystem
  staging_dir: "{staging_dir}"
  use_account_subfolders: {str(use_account_subfolders).lower()}
  copy_manifest: true
  overwrite: false
  create_staging_dir: false
""")
    return path


class FakeMailbox:
    instances = []

    def __init__(self, config, root):
        self.config = config
        self.root = root
        self.calls = []
        self.__class__.instances.append(self)

    def list_pending(self):
        self.calls.append("list_pending")
        return (
            MessageReference(self.config.mailbox, "123", "41", "<a@example.invalid>",
                             "Subject A", "sender@example.invalid",
                             "2026-06-25T10:00:00+00:00"),
            MessageReference(self.config.mailbox, "123", "42", "<b@example.invalid>",
                             "Subject B", "sender@example.invalid",
                             "2026-06-25T10:01:00+00:00"),
        )

    def detect_attachments(self, message):
        raise AssertionError("multi-account scan must not download or inspect attachments")

    def download_attachments(self, message):
        raise AssertionError("multi-account scan must not download attachments")

    def acknowledge(self, message):
        raise AssertionError("multi-account scan must not acknowledge messages")


class FakeProcessMailbox(FakeMailbox):
    attachments = (DetectedAttachment(1, "report.pdf", "application/pdf", b"%PDF"),)

    def detect_attachments(self, message):
        self.calls.append(("detect_attachments", message.message_uid))
        return self.attachments


class FakeScanner:
    def __init__(self, verdict):
        self.verdict = verdict

    @property
    def available(self):
        return True

    def scan(self, path):
        return LocalScanResult("fake", self.verdict, f"fake {self.verdict.value}")


class FailingScanner:
    @property
    def available(self):
        return True

    def scan(self, path):
        raise RuntimeError("boom")


class FakeAckMailbox:
    instances = []

    def __init__(self, account, *, input_present=True, done_present=False,
                 fail=False, fail_message="ack boom"):
        self.account = account
        self.input_present = input_present
        self.done_present = done_present
        self.fail = fail
        self.fail_message = fail_message
        self.calls = []
        self.__class__.instances.append(self)

    def input_contains_uid(self, uid):
        self.calls.append(("input_contains_uid", self.account.account_alias, uid))
        return self.input_present

    def done_contains_message_id(self, message_id):
        self.calls.append(("done_contains_message_id", self.account.account_alias, message_id))
        return self.done_present

    def add_done_label_only(self, uid):
        self.calls.append(("add_done_label_only", self.account.account_alias,
                           self.account.done_folder, uid))
        if self.fail:
            raise RuntimeError(self.fail_message)

    def move_to_done_label(self, uid, message_id):
        self.calls.append(("move_to_done_label", self.account.account_alias,
                           self.account.input_folder, self.account.done_folder, uid,
                           message_id))
        if self.fail:
            raise RuntimeError(self.fail_message)


class FakeArchiveStatusClient:
    def __init__(self, statuses=None, *, error=None):
        self.statuses_by_id = statuses or {}
        self.error = error
        self.calls = []

    def statuses(self, inbox_ids):
        self.calls.append(tuple(inbox_ids))
        if self.error:
            raise RuntimeError(self.error)
        return {inbox_id: self.statuses_by_id.get(inbox_id, "") for inbox_id in inbox_ids}


def test_loads_multi_account_yaml_without_secret_values(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    assert [account.account_alias for account in accounts] == ["account_1", "disabled_box"]
    assert accounts[0].email == "account.1@example.invalid"
    assert accounts[0].max_messages == 7
    assert accounts[0].password_env == "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD"


def test_attachment_identity_is_canonical_when_uidvalidity_is_missing():
    attachment_id = canonical_attachment_id(None, "20", 1)

    assert attachment_id == "att-unknown-20-1"


def test_scaffold_local_config_is_valid_and_secret_free(tmp_path):
    config_path = tmp_path / "accounts.local.yaml"
    content = scaffold_local_config(
        email="account.1@example.com",
        staging_dir=tmp_path / "staging",
    )
    config_path.write_text(content, encoding="utf-8")

    accounts = load_multi_account_config(config_path)
    storage = load_storage_config(config_path)
    assert load_rules(config_path).default_action == "include"
    assert accounts[0].account_alias == "account_1"
    assert accounts[0].username_env == "VIRGILIO_IMAP_ACCOUNT_1_USERNAME"
    assert storage.staging_dir == tmp_path / "staging"
    assert "password-app-o-token" in content
    assert "TOP_SECRET" not in content
    assert "client_secret.json" in content
    assert "use_account_subfolders: false" in content


def test_scaffold_local_config_requires_absolute_staging_dir():
    with pytest.raises(MultiAccountConfigError, match="absolute path"):
        scaffold_local_config(
            email="account.1@example.com",
            staging_dir=Path("staging"),
        )


def test_rejects_duplicate_alias(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("""accounts:
  - account_alias: same_alias
    email: a@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_A_USERNAME
    password_env: VIRGILIO_A_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
  - account_alias: same_alias
    email: b@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_B_USERNAME
    password_env: VIRGILIO_B_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
""", encoding="utf-8")
    with pytest.raises(MultiAccountConfigError, match="unique"):
        load_multi_account_config(path)


def test_missing_env_vars_fail_closed_without_network(tmp_path):
    account = LocalImapAccount(
        account_alias="account_1",
        email="account.1@example.invalid",
        provider_hint="gmail_workspace",
        imap_host="imap.gmail.com",
        imap_port=993,
        username_env="VIRGILIO_IMAP_ACCOUNT_1_USERNAME",
        password_env="VIRGILIO_IMAP_ACCOUNT_1_PASSWORD",
        input_folder="Virgilio/da-traghettare",
        done_folder="Virgilio/traghettate",
        error_folder="Virgilio/errore",
    )
    calls = []
    result = MultiAccountReadonlyScanner(
        [account],
        paths=LocalDataPaths(tmp_path / ".local_data"),
        environ={},
        mailbox_factory=lambda *_: calls.append("network"),
    ).scan(dry_run=True)
    assert result[0].status == "error"
    assert "VIRGILIO_IMAP_ACCOUNT_1_USERNAME" in result[0].error
    assert calls == []


def test_dry_run_scans_enabled_accounts_without_writing_state(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=True)
    assert [(item.account_alias, item.status, item.messages_seen) for item in result] == [
        ("account_1", "ok", 2),
        ("disabled_box", "disabled", 0),
    ]
    assert paths.state_db.is_file()
    assert len(FakeMailbox.instances) == 1
    assert FakeMailbox.instances[0].config.password == "secret"


def test_non_dry_run_records_account_alias_separately(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=False)
    assert result[0].status == "ok"
    with sqlite3.connect(paths.state_db) as db:
        runs = db.execute("SELECT account_alias,messages_seen,attachments_seen,status FROM runs").fetchall()
        messages = db.execute("SELECT account_alias,message_uid,mailbox FROM messages ORDER BY message_uid").fetchall()
        attachments = db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    assert runs == [("account_1", 2, 0, "completed")]
    assert messages == [
        ("account_1", "41", "Virgilio/da-traghettare"),
        ("account_1", "42", "Virgilio/da-traghettare"),
    ]
    assert attachments == 0


def process(tmp_path, *, dry_run=False, scanner=None):
    FakeProcessMailbox.instances.clear()
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountImapProcessor(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
        scanner=scanner,
    ).process(dry_run=dry_run)
    return result, paths


def test_process_dry_run_lists_candidate_attachments_without_files_or_db(tmp_path):
    result, paths = process(tmp_path, dry_run=True)
    assert len(result) == 2
    assert result[0].account_alias == "account_1"
    assert result[0].original_filename == "report.pdf"
    assert result[0].quarantine_status == "quarantined_unverified"
    assert result[0].saved is False
    assert paths.state_db.is_file()


def test_process_writes_quarantine_manifest_and_sqlite_per_account(tmp_path):
    result, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    assert result[0].quarantine_status == "ready_for_caronte"
    assert result[0].saved is True
    assert result[0].manifest_path
    manifest_path = paths.root / result[0].manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["connector_type"] == "local_imap"
    assert manifest["account_alias"] == "account_1"
    assert manifest["source_email"] == "user@example.invalid"
    assert manifest["source_sender"] == "sender@example.invalid"
    assert manifest["source_mailbox"] == "Virgilio/da-traghettare"
    assert manifest["source_message_uid"] == "41"
    assert manifest["source_message_id"] == "<a@example.invalid>"
    assert manifest["source_message_date"] == "2026-06-25T10:00:00+00:00"
    assert manifest["source_thread_id"] is None
    assert manifest["attachment_id"] == result[0].attachment_id
    assert manifest["file_extension"] == ".pdf"
    assert manifest["sha256"] == result[0].sha256
    assert manifest["scan_engine"] == "fake"
    assert manifest["scan_result"] == "clean"
    assert manifest["policy_included"] is True
    assert manifest["policy_rule"] is None
    assert manifest["status_reason"] == "fake clean"
    assert manifest["fingerprint"] == result[0].fingerprint
    assert manifest["audit_trail"][-1]["action"] == "manifest_created"
    assert all(item["machine_id"] for item in manifest["audit_trail"])
    assert len(list((paths.root / "accounts" / "account_1" / "quarantine" / "ready").rglob("*.pdf"))) == 2
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT fingerprint FROM attachments").fetchone()[0] == result[0].fingerprint
        rows = db.execute("""SELECT a.account_alias,a.attachment_id,a.source_email,
            a.status,a.manifest_path,m.message_uid,m.message_id,m.subject
            FROM attachments a JOIN messages m ON m.id=a.message_id
            ORDER BY m.message_uid""").fetchall()
    assert rows[0][0] == "account_1"
    assert rows[0][2] == "user@example.invalid"
    assert rows[0][3] == "ready_for_caronte"
    assert rows[0][4] == result[0].manifest_path
    assert rows[0][5:] == ("41", "<a@example.invalid>", "Subject A")


def test_process_falls_back_to_config_email_when_username_is_not_an_email(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountImapProcessor(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "imap-user",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
        scanner=FakeScanner(ScanVerdict.CLEAN),
    ).process(dry_run=False)
    exported = next(item for item in result if item.manifest_path)
    manifest_path = paths.root / exported.manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_email"] == "account.1@example.invalid"


def test_process_is_idempotent_for_same_attachment_id_and_sha(tmp_path):
    result1, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    result2, _ = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    assert result2[0].attachment_id == result1[0].attachment_id
    assert result2[0].saved is False
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2


def test_scanner_and_processor_reuse_message_identity_across_cycles(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    environ = {
        "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
        "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
    }
    scanner = MultiAccountReadonlyScanner(
        accounts, paths=paths, environ=environ,
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    )
    processor = MultiAccountImapProcessor(
        accounts, paths=paths, environ=environ,
        mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
        scanner=FakeScanner(ScanVerdict.CLEAN),
    )

    scanner.scan(dry_run=False)
    processor.process(dry_run=False)
    scanner.scan(dry_run=False)
    processor.process(dry_run=False)

    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2


def test_message_identity_falls_back_to_message_id_without_uidvalidity(tmp_path):
    paths = LocalDataPaths(tmp_path / ".local_data")
    store = ReadonlyStateStore(paths.state_db)
    store.initialize()
    first_run = store.start_run("account_1")
    second_run = store.start_run("account_1")
    first = MessageReference(
        "INBOX", None, "41", "<stable@example.invalid>", "First", "a@example.invalid",
        "2026-07-28T10:00:00+02:00",
    )
    second = MessageReference(
        "INBOX", None, "84", "<stable@example.invalid>", "Second", "a@example.invalid",
        "2026-07-28T10:00:00+02:00",
    )

    first_id = store.find_or_add_message(first_run, first, account_alias="account_1")
    second_id = store.find_or_add_message(second_run, second, account_alias="account_1")

    assert second_id == first_id
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_process_reacquires_duplicate_when_local_file_is_not_valid(tmp_path, damage):
    first, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    with sqlite3.connect(paths.state_db) as db:
        relative_path = db.execute(
            "SELECT relative_path FROM attachments WHERE attachment_id=?",
            (first[0].attachment_id,),
        ).fetchone()[0]
    local_file = paths.root / relative_path
    if damage == "missing":
        local_file.unlink()
    else:
        local_file.write_bytes(b"corrupt")

    recovered, _ = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))

    assert recovered[0].saved is True
    assert recovered[0].reason == "fake clean"
    assert local_file.read_bytes() == b"%PDF"
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2
        row = db.execute("""SELECT status,relative_path,sha256 FROM attachments
            WHERE attachment_id=?""", (first[0].attachment_id,)).fetchone()
    assert row == ("ready_for_caronte", relative_path, first[0].sha256)


def test_process_detects_attachment_id_sha_conflict(tmp_path):
    result1, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    FakeProcessMailbox.attachments = (DetectedAttachment(1, "report.pdf", "application/pdf", b"different"),)
    try:
        result2, _ = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    finally:
        FakeProcessMailbox.attachments = (DetectedAttachment(1, "report.pdf", "application/pdf", b"%PDF"),)
    assert result2[0].attachment_id == result1[0].attachment_id
    assert result2[0].quarantine_status == "error"
    assert "different sha256" in result2[0].error
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2


def test_process_maps_scanner_verdicts_prudently(tmp_path):
    infected, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.INFECTED))
    assert infected[0].quarantine_status == "rejected_malware"
    assert len(list((paths.root / "accounts" / "account_1" / "quarantine" / "rejected").rglob("*.pdf"))) == 2
    failed, _ = process(tmp_path / "failed", scanner=FailingScanner())
    assert failed[0].quarantine_status == "scan_failed"
    assert failed[0].scan_result == "failed"


def ready_fixture(tmp_path):
    result, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    assert all(item.quarantine_status == "ready_for_caronte" for item in result)
    return result, paths


def stage(paths, staging_dir, *, dry_run=False, use_account_subfolders=True):
    config = LocalStorageConfig(
        "local_filesystem", staging_dir,
        use_account_subfolders=use_account_subfolders,
        copy_manifest=True, overwrite=False, create_staging_dir=False,
    )
    return LocalFilesystemStorageAdapter(
        state_db=paths.state_db, local_data_root=paths.root, config=config
    ).stage_ready(dry_run=dry_run)


def test_storage_config_validation(tmp_path):
    with pytest.raises(MultiAccountConfigError, match="staging_dir"):
        LocalStorageConfig("local_filesystem", None)
    with pytest.raises(MultiAccountConfigError, match="absolute path"):
        LocalStorageConfig("local_filesystem", Path("relative"))
    with pytest.raises(MultiAccountConfigError, match="unsupported"):
        LocalStorageConfig("ftp", tmp_path)
    staging = tmp_path / "staging"
    path = write_storage_config(tmp_path, staging, use_account_subfolders=False)
    config = load_storage_config(path)
    assert config.staging_dir == staging
    assert config.use_account_subfolders is False


def test_storage_missing_directory_errors(tmp_path):
    _, paths = ready_fixture(tmp_path)
    with pytest.raises(StorageAdapterError, match="does not exist"):
        stage(paths, tmp_path / "missing")


def test_storage_dry_run_does_not_copy_or_update_sqlite(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    results = stage(paths, staging, dry_run=True)
    assert len(results) == 2
    assert all(item.status == "planned" and item.copied is False for item in results)
    assert not list(staging.rglob("*"))
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT DISTINCT status FROM attachments").fetchall() == [("ready_for_caronte",)]


def test_storage_real_copy_manifest_hash_and_sqlite(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    results = stage(paths, staging)
    assert len(results) == 2
    first = results[0]
    assert first.status == "staged_storage"
    assert first.copied is True
    staged_file = staging / first.staged_path
    staged_manifest = staging / first.staged_manifest_path
    assert staged_file.is_file()
    assert staged_manifest.is_file()
    assert staged_file.read_bytes() == b"%PDF"
    assert (paths.root / first.source_relative_path).is_file()
    manifest = json.loads(staged_manifest.read_text(encoding="utf-8"))
    assert manifest["storage_adapter"] == "local_filesystem"
    assert manifest["staged_filename"] == staged_file.name
    assert manifest["account_alias"] == "account_1"
    assert manifest["source_mailbox"] == "Virgilio/da-traghettare"
    assert manifest["status_reason"] == "fake clean"
    forbidden = {"password", "token", "file_bytes", "base64", "content", "raw"}
    assert not (forbidden & set(manifest))
    with sqlite3.connect(paths.state_db) as db:
        rows = db.execute("""SELECT status,storage_adapter,staged_path,
            staging_manifest_path,staged_filename FROM attachments ORDER BY id""").fetchall()
    assert rows[0][0] == "staged_storage"
    assert rows[0][1] == "local_filesystem"
    assert rows[0][2] == first.staged_path
    assert rows[0][3] == first.staged_manifest_path
    assert rows[0][4] == staged_file.name


def test_storage_account_subfolders_can_be_disabled(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    result = stage(paths, staging, use_account_subfolders=False)[0]
    assert "/" not in result.staged_path
    assert (staging / result.staged_path).is_file()


def test_storage_defaults_to_flat_limbo_with_collision_safe_filename(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    result = LocalFilesystemStorageAdapter(
        state_db=paths.state_db,
        local_data_root=paths.root,
        config=LocalStorageConfig("local_filesystem", staging),
    ).stage_ready(dry_run=False)[0]
    assert "/" not in result.staged_path
    assert result.staged_path.startswith(f"{result.account_alias}__{result.attachment_id}__")
    assert (staging / result.staged_path).is_file()


def test_storage_idempotency_and_conflict(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    first = stage(paths, staging)[0]
    retry = stage(paths, staging)
    assert retry[0].status == "already_staged"
    with sqlite3.connect(paths.state_db) as db:
        db.execute("UPDATE attachments SET status='ready_for_caronte' WHERE id=1")
        db.commit()
    same_hash = stage(paths, staging)[0]
    assert same_hash.status == "staged_storage"
    staged_file = staging / first.staged_path
    staged_file.write_bytes(b"different")
    with sqlite3.connect(paths.state_db) as db:
        db.execute("UPDATE attachments SET status='ready_for_caronte' WHERE id=1")
        db.commit()
    conflict = stage(paths, staging)[0]
    assert conflict.status == "staging_conflict"
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT status FROM attachments WHERE id=1").fetchone()[0] == "staging_conflict"
        assert db.execute("""SELECT COUNT(*) FROM audit_events
            WHERE action='staging_conflict' AND status='staging_conflict'""").fetchone()[0] == 1


def test_storage_failure_is_persisted_as_actionable_audit_event(tmp_path):
    ready, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    with sqlite3.connect(paths.state_db) as db:
        relative_path = db.execute("SELECT relative_path FROM attachments WHERE id=1").fetchone()[0]
    (paths.root / relative_path).unlink()

    failed = stage(paths, staging)[0]

    assert failed.status == "staging_failed"
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT status FROM attachments WHERE id=1").fetchone()[0] == "staging_failed"
        event = db.execute("""SELECT action,status,details_json FROM audit_events
            WHERE action='staging_failed' ORDER BY id DESC LIMIT 1""").fetchone()
    assert event[:2] == ("staging_failed", "staging_failed")
    assert "quarantine source file is missing" in event[2]


def test_stage_ready_attachments_cli_dry_run(tmp_path, monkeypatch, capsys):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    config = write_storage_config(tmp_path / "cli", staging)
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(paths.root))
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "stage-ready-attachments",
        "--config", str(config), "--dry-run",
    ])
    from virgilio_connector.__main__ import main
    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["status"] == "planned"
    assert not list(staging.rglob("*"))


def test_stage_ready_attachments_cli_real(tmp_path, monkeypatch, capsys):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    config = write_storage_config(tmp_path / "cli-real", staging)
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(paths.root))
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "stage-ready-attachments",
        "--config", str(config),
    ])
    from virgilio_connector.__main__ import main
    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["status"] == "staged_storage"
    assert (staging / output[0]["staged_path"]).is_file()
    assert (staging / output[0]["staged_manifest_path"]).is_file()


def staged_fixture(tmp_path):
    _, paths = ready_fixture(tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    stage(paths, staging)
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    return accounts, paths


def complete(paths, accounts, *, dry_run=False, mailbox_factory=None):
    return LocalCompletionRunner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=mailbox_factory or (lambda account: FakeAckMailbox(account)),
    ).complete(dry_run=dry_run)


def controlled_ack(paths, accounts, *, dry_run=False, mailbox_factory=None):
    return ControlledAckRunner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=mailbox_factory or (lambda account: FakeAckMailbox(account)),
    ).run(dry_run=dry_run)


def test_operational_completion_waits_for_da_archiviare_handoff(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    mailbox_calls = []

    def mailbox_factory(account):
        mailbox_calls.append(account.account_alias)
        return FakeAckMailbox(account)

    status_client = FakeArchiveStatusClient({"inbox-1": "da_lavorare"})
    runner = LocalCompletionRunner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=mailbox_factory,
        require_da_archiviare=True,
        archive_status_client=status_client,
    )

    blocked = runner.complete(dry_run=False)

    assert blocked[0].status == "completion_skipped"
    assert blocked[0].reason == "message has attachments not delivered to Da archiviare"
    assert mailbox_calls == []

    with sqlite3.connect(paths.state_db) as db:
        attachments = db.execute(
            """SELECT attachment_id,account_alias,fingerprint
               FROM attachments WHERE status='staged_storage' ORDER BY id"""
        ).fetchall()
        db.executemany(
            """INSERT INTO audit_events(
                 created_at,machine_id,account_alias,entity_type,entity_id,
                 fingerprint,action,status,details_json
               ) VALUES(datetime('now'),'caronte-test',?,'attachment',?,?,
                        'da_archiviare_intake','idempotent',?)""",
            [(row[1], row[0], row[2], json.dumps({"inbox_id": f"inbox-{index}"}))
             for index, row in enumerate(attachments, start=1)],
        )
        db.commit()

    pending = runner.complete(dry_run=False)
    assert all(item.status == "completion_skipped" for item in pending)
    assert all("archiviazione finale" in item.reason for item in pending)
    assert mailbox_calls == []

    with sqlite3.connect(paths.state_db) as db:
        audit_before_quiet_poll = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    reports_before_quiet_poll = set((paths.root / "reports").glob("completion_report_*.json"))
    quiet_pending = runner.complete(
        dry_run=False, write_report=False, record_skipped=False
    )
    with sqlite3.connect(paths.state_db) as db:
        audit_after_quiet_poll = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    assert all(item.status == "completion_skipped" for item in quiet_pending)
    assert audit_after_quiet_poll == audit_before_quiet_poll
    assert set((paths.root / "reports").glob("completion_report_*.json")) == reports_before_quiet_poll

    status_client.statuses_by_id = {
        f"inbox-{index}": "archiviato" for index in range(1, len(attachments) + 1)
    }
    completed = runner.complete(dry_run=False)

    assert all(item.status == "completed" for item in completed)
    assert mailbox_calls == ["account_1", "account_1"]


def test_operational_completion_stays_retryable_when_archive_status_fails(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    with sqlite3.connect(paths.state_db) as db:
        rows = db.execute("""SELECT attachment_id,account_alias,fingerprint
            FROM attachments WHERE status='staged_storage' ORDER BY id""").fetchall()
        db.executemany("""INSERT INTO audit_events(
            created_at,machine_id,account_alias,entity_type,entity_id,fingerprint,
            action,status,details_json
        ) VALUES(datetime('now'),'caronte-test',?,'attachment',?,?,
                 'da_archiviare_intake','created',?)""", [
            (row[1], row[0], row[2], json.dumps({"inbox_id": f"inbox-{index}"}))
            for index, row in enumerate(rows, start=1)
        ])
        db.commit()
    calls = []
    runner = LocalCompletionRunner(
        accounts, paths=paths,
        mailbox_factory=lambda account: calls.append(account),
        require_da_archiviare=True,
        archive_status_client=FakeArchiveStatusClient(error="status unavailable"),
    )

    result = runner.complete(dry_run=False)

    assert all(item.status == "completion_skipped" for item in result)
    assert all("verifica archiviazione" in item.reason for item in result)
    assert calls == []


def mark_candidate_events_exported(paths, accounts, *, leave_pending=0):
    preview = controlled_ack(paths, accounts, dry_run=True)
    attachment_ids = {
        attachment_id
        for item in preview.results
        if item.status == "planned"
        for attachment_id in item.staged_attachments
    }
    event_ids = [
        row["event_id"] for row in operational_event_rows(paths.state_db)
        if row["attachment_id"] in attachment_ids
    ]
    exported = event_ids[:-leave_pending] if leave_pending else event_ids
    with sqlite3.connect(paths.state_db) as db:
        db.executemany("""INSERT INTO local_export_status(
            event_id,target_adapter,exported_at,export_result,error_type
        ) VALUES(?,?,?,?,?)""", [
            (
                event_id,
                BucolicheAppendOnlyAdapter.TARGET,
                "2026-06-30T00:00:01+00:00",
                "exported",
                None,
            )
            for event_id in exported
        ])
        db.commit()
    return len(event_ids)


def test_completion_dry_run_plans_without_imap_or_sqlite_changes(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    calls = []
    result = complete(paths, accounts, dry_run=True,
                      mailbox_factory=lambda account: calls.append(account))
    assert result[0].status == "planned"
    assert calls == []
    assert result[0].report_path is None
    with sqlite3.connect(paths.state_db) as db:
        states = db.execute("SELECT DISTINCT message_state FROM messages").fetchall()
    assert states == [("open",)]


def test_controlled_ack_dry_run_does_not_open_imap_in_write_mode(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    mark_candidate_events_exported(paths, accounts)
    calls = []
    result = controlled_ack(paths, accounts, dry_run=True,
                            mailbox_factory=lambda account: calls.append(account))
    assert result.status == "dry_run"
    assert calls == []


def test_completion_real_ack_updates_sqlite_and_report(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    FakeAckMailbox.instances.clear()
    result = complete(paths, accounts)
    assert result[0].status == "completed"
    assert result[0].report_path
    assert FakeAckMailbox.instances[0].calls == [
        ("input_contains_uid", "account_1", "41"),
        ("add_done_label_only", "account_1", "Virgilio/traghettate", "41"),
    ]
    all_calls = [str(call).upper() for inst in FakeAckMailbox.instances for call in inst.calls]
    for forbidden in ("EXPUNGE", "STORE", "DELETE", "MOVE", "SEEN"):
        assert not any(forbidden in call for call in all_calls)
    report = json.loads((paths.root / result[0].report_path).read_text(encoding="utf-8"))
    assert report["messages_completed"] == 2
    assert report["results"][0]["account_alias"] == "account_1"
    assert report["results"][0]["staged_attachments"]
    assert "password" not in json.dumps(report).lower()
    assert "base64" not in json.dumps(report).lower()
    with sqlite3.connect(paths.state_db) as db:
        rows = db.execute("""SELECT message_state,ack_strategy,ack_result,
            ack_attempted_at,ack_completed_at,completed_at,completion_report_path
            FROM messages ORDER BY id""").fetchall()
        attachments = db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    assert rows[0][0] == "completed"
    assert rows[0][1] == "add_done_label_only"
    assert rows[0][2] in {"completed", "already_acked"}
    assert rows[0][3] is not None
    assert rows[0][4] is not None
    assert rows[0][5] is not None
    assert rows[0][6] == result[0].report_path
    assert attachments == 2
    assert result[0].reason == "marcata come traghettata; messaggio non rimosso dalla cartella input"


def test_completion_move_strategy_removes_input_label_and_records_result(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    account = accounts[0]
    moving = (LocalImapAccount(
        account_alias=account.account_alias,
        email=account.email,
        provider_hint=account.provider_hint,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        username_env=account.username_env,
        password_env=account.password_env,
        input_folder=account.input_folder,
        done_folder=account.done_folder,
        error_folder=account.error_folder,
        enabled=account.enabled,
        max_messages=account.max_messages,
        ack_enabled=True,
        ack_strategy="move_to_done_label",
    ),)
    FakeAckMailbox.instances.clear()
    result = complete(paths, moving)
    assert result[0].status == "completed"
    assert result[0].reason == "marcata come traghettata; etichetta input rimossa"
    assert FakeAckMailbox.instances[0].calls == [
        ("input_contains_uid", "account_1", "41"),
        ("move_to_done_label", "account_1", "Virgilio/da-traghettare",
         "Virgilio/traghettate", "41", "<a@example.invalid>"),
    ]
    with sqlite3.connect(paths.state_db) as db:
        strategy, ack_result = db.execute(
            "SELECT ack_strategy,ack_result FROM messages WHERE id=1"
        ).fetchone()
    assert strategy == "move_to_done_label"
    assert ack_result == "completed"


def test_completion_skips_blocking_attachment_states(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    with sqlite3.connect(paths.state_db) as db:
        db.execute("UPDATE attachments SET status='staging_failed' WHERE id=1")
        db.commit()
    result = complete(paths, accounts)
    assert result[0].status == "completion_skipped"
    assert "blocking" in result[0].reason


def test_completion_ack_disabled_skips_without_imap(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    disabled = (LocalImapAccount(
        account_alias=accounts[0].account_alias,
        email=accounts[0].email,
        provider_hint=accounts[0].provider_hint,
        imap_host=accounts[0].imap_host,
        imap_port=accounts[0].imap_port,
        username_env=accounts[0].username_env,
        password_env=accounts[0].password_env,
        input_folder=accounts[0].input_folder,
        done_folder=accounts[0].done_folder,
        error_folder=accounts[0].error_folder,
        ack_enabled=False,
        ack_strategy="add_done_label_only",
    ),)
    calls = []
    result = complete(paths, disabled, mailbox_factory=lambda account: calls.append(account))
    assert result[0].status == "completion_skipped"
    assert "ack_enabled" in result[0].reason
    assert calls == []


def test_completion_retry_after_completed_is_idempotent(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    first = complete(paths, accounts)
    retry = complete(paths, accounts, mailbox_factory=lambda account: (_ for _ in ()).throw(AssertionError("no ack")))
    assert first[0].status == "completed"
    assert retry[0].status == "already_completed"


def test_completion_already_in_done_folder(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    result = complete(paths, accounts,
        mailbox_factory=lambda account: FakeAckMailbox(account, input_present=False, done_present=True))
    assert result[0].status == "already_acked"
    assert "gia presente in done_folder" in result[0].reason
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT message_state FROM messages WHERE id=1").fetchone()[0] == "completed"


def test_completion_ack_failure_surfaces_copy_diagnostics(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    result = complete(
        paths,
        accounts,
        mailbox_factory=lambda account: FakeAckMailbox(
            account,
            fail=True,
            fail_message=("done_folder_not_found_in_imap_list: done_folder='Virgilio/traghettate'; "
                          "verify exact IMAP name and 'Mostra in IMAP'"),
        ),
    )
    assert result[0].status == "ack_failed"
    assert "done_folder_not_found_in_imap_list" in result[0].reason
    assert "Mostra in IMAP" in result[0].reason


def test_completion_ack_failure_does_not_block_other_account(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    with sqlite3.connect(paths.state_db) as db:
        db.execute("""INSERT INTO runs(started_at,dry_run,status,messages_seen,attachments_seen,account_alias)
            VALUES('now',0,'completed',1,1,'second_box')""")
        run_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, "second_box", "INBOX", "222", "99", "<second@example.invalid>",
             "Second", "sender@example.invalid", "2026-06-25T10:00:00+00:00"))
        message_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,relative_path,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_id, "second_box", "second-222-99-1", "second@example.invalid", 1,
             "x.pdf", "x.pdf", "application/pdf", 1, "a" * 64, "staged_storage",
             "accounts/account_1/quarantine/ready/41/001-report.pdf", "test", "now"))
        db.commit()
    second = LocalImapAccount(
        account_alias="second_box", email="second@example.invalid",
        provider_hint="generic", imap_host="imap.example.invalid", imap_port=993,
        username_env="VIRGILIO_IMAP_ACCOUNT_1_USERNAME",
        password_env="VIRGILIO_IMAP_ACCOUNT_1_PASSWORD",
        input_folder="INBOX", done_folder="done", error_folder="error",
        ack_enabled=True, ack_strategy="add_done_label_only",
    )
    results = complete(paths, (accounts[0], second),
        mailbox_factory=lambda account: FakeAckMailbox(account, fail=account.account_alias == "account_1"))
    statuses = {item.account_alias: item.status for item in results}
    assert statuses["account_1"] == "ack_failed"
    assert statuses["second_box"] == "completed"


def test_complete_staged_messages_cli_dry_run(tmp_path, monkeypatch, capsys):
    accounts, paths = staged_fixture(tmp_path)
    config = write_config(tmp_path / "cli-complete")
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(paths.root))
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "complete-staged-messages",
        "--config", str(config), "--dry-run",
    ])
    from virgilio_connector.__main__ import main
    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["status"] == "planned"


def test_controlled_ack_dry_run_reports_gate_ready(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    mark_candidate_events_exported(paths, accounts)
    result = controlled_ack(paths, accounts, dry_run=True)
    assert result.status == "dry_run"
    assert result.gate_status == "READY"
    assert result.messages_planned == 2
    assert result.pending_export_events == 0
    assert result.local_conflicts == 0
    assert result.results[0].status == "planned"


def test_controlled_ack_real_run_blocks_when_export_is_pending(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    total = mark_candidate_events_exported(paths, accounts, leave_pending=1)
    calls = []
    result = controlled_ack(paths, accounts, mailbox_factory=lambda account: calls.append(account))
    assert result.status == "blocked"
    assert result.gate_status == "BLOCKED"
    assert result.pending_export_events == 1
    assert total > 1
    assert any("export-to-bucoliche" in item for item in result.errors)
    assert calls == []


def test_controlled_ack_real_run_blocks_on_candidate_conflict(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    mark_candidate_events_exported(paths, accounts)
    with sqlite3.connect(paths.state_db) as db:
        base = db.execute("""SELECT fingerprint,attachment_id,relative_path
            FROM attachments ORDER BY id LIMIT 1""").fetchone()
    with sqlite3.connect(paths.state_db) as db:
        db.execute("""INSERT INTO runs(started_at,dry_run,status,messages_seen,attachments_seen,account_alias)
            VALUES('now',0,'completed',1,1,'account_1')""")
        run_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, "account_1", "Virgilio/da-traghettare", "123", "77",
             "<dup@example.invalid>", "Dup", "sender@example.invalid", "2026-06-25T10:00:00+00:00"))
        message_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,relative_path,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_id, "account_1", "dup-1", "user@example.invalid", 1, "dup.pdf", "dup.pdf",
             "application/pdf", 1, "b" * 64, "staged_storage",
             base[2], "dup", base[0], "now"))
        db.commit()
    calls = []
    result = controlled_ack(paths, accounts, mailbox_factory=lambda account: calls.append(account))
    assert result.status == "blocked"
    assert result.local_conflicts >= 1
    assert any("check-local-conflicts" in item for item in result.errors)
    assert calls == []


def test_controlled_ack_real_run_completes_after_export_gate_is_satisfied(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    mark_candidate_events_exported(paths, accounts)
    result = controlled_ack(paths, accounts)
    assert result.status == "completed"
    assert result.gate_status == "READY"
    assert result.results[0].status == "completed"


def test_ack_completed_messages_cli_dry_run(tmp_path, monkeypatch, capsys):
    accounts, paths = staged_fixture(tmp_path)
    mark_candidate_events_exported(paths, accounts)
    config = write_config(tmp_path / "cli-ack")
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(paths.root))
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "ack-completed-messages",
        "--config", str(config), "--dry-run",
    ])
    from virgilio_connector.__main__ import main
    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "dry_run"
    assert output["gate_status"] == "READY"


class FakePhase:
    def __init__(self, name, log, result=(), fail=False):
        self.name = name
        self.log = log
        self.result = result
        self.fail = fail

    def scan(self, dry_run):
        self.log.append((self.name, dry_run))
        if self.fail:
            raise RuntimeError("phase boom")
        return self.result

    def process(self, dry_run):
        self.log.append((self.name, dry_run))
        if self.fail:
            raise RuntimeError("phase boom")
        return self.result

    def stage_ready(self, dry_run):
        self.log.append((self.name, dry_run))
        if self.fail:
            raise RuntimeError("phase boom")
        return self.result

    def complete(self, dry_run, **kwargs):
        self.log.append((self.name, dry_run))
        if self.fail:
            raise RuntimeError("phase boom")
        return self.result


class FakeHandoffPhase:
    def __init__(self, log, result=()):
        self.log = log
        self.result = result

    def deliver(self, storage_results, dry_run):
        self.log.append(("handoff", dry_run))
        return self.result


def test_resume_pending_retries_handoff_and_completion_without_reacquisition(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    runner = LocalPipelineRunner(
        accounts,
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        handoff_factory=lambda: FakeHandoffPhase(log),
        completion_factory=lambda: FakePhase("completion", log),
    )

    runner.resume_pending(dry_run=False)

    assert log == [
        ("storage", False),
        ("handoff", False),
        ("completion", False),
    ]


@dataclass(frozen=True)
class FakeRegistryResult:
    status: str
    errors: tuple[str, ...] = ()


class FakeRegistryPhase:
    def __init__(self, log, result):
        self.log = log
        self.result = result

    def export(self, dry_run):
        self.log.append(("registry", dry_run))
        return self.result


def test_pipeline_dry_run_no_report_and_order(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    runner = LocalPipelineRunner(
        accounts, paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        completion_factory=lambda: FakePhase("completion", log),
        config_path=tmp_path / "accounts.yaml",
    )
    result = runner.run(dry_run=True)
    assert result.status == "completed_with_warnings"
    assert result.report_path is None
    assert result.human_summary[0] == "Esito pipeline: completed_with_warnings (dry-run)"
    assert log == [("scan", True), ("process", True), ("storage", True), ("completion", True)]
    assert (tmp_path / ".local_data" / "state.db").is_file()


def test_pipeline_reports_real_phase_changes_and_counts_when_known(tmp_path):
    log = []
    runner = LocalPipelineRunner(
        (), paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        completion_factory=lambda: FakePhase("completion", log),
    )
    progress = []

    runner.run(dry_run=True, progress=progress.append)

    assert [item["phase"] for item in progress[:3]] == [
        "Controllo delle caselle", "Elaborazione dei documenti", "Preparazione dei documenti",
    ]
    assert progress[-1] == {
        "phase": "Elaborazione dei documenti", "found": 0, "processed": 0, "remaining": 0,
    }


def test_pipeline_warns_when_messages_have_no_detectable_attachments(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    scan = MultiAccountScanResult(
        "account_1", "account.1@example.invalid", "gmail_workspace", True, "ok", 1,
    )
    log = []
    runner = LocalPipelineRunner(
        accounts, paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log, (scan,)),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        completion_factory=lambda: FakePhase("completion", log),
    )

    result = runner.run(dry_run=False)
    report = json.loads(
        (tmp_path / ".local_data" / result.report_path).read_text(encoding="utf-8")
    )

    assert result.status == "completed_with_warnings"
    assert "acquisition: messages_found_without_detectable_attachments" in result.warnings
    assert any(
        "mail trovate ma nessun allegato acquisibile" in line.lower()
        for line in result.human_summary
    )
    assert report["messages_found"] == 1
    assert report["attachments_processed"] == 0


def test_pipeline_real_report_and_error_collection(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    runner = LocalPipelineRunner(
        accounts, paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log, fail=True),
        storage_factory=lambda: FakePhase("storage", log),
        completion_factory=lambda: FakePhase("completion", log),
    )
    result = runner.run(dry_run=False)
    assert result.status == "completed_with_errors"
    assert result.report_path
    assert log == [("scan", False), ("process", False), ("storage", False), ("completion", False)]
    report = json.loads((tmp_path / ".local_data" / result.report_path).read_text(encoding="utf-8"))
    assert report["errors"]
    assert report["human_summary"][0] == "Esito pipeline: completed_with_errors (run reale)"
    assert any(line.startswith("Errore: process: RuntimeError: phase boom")
               for line in report["human_summary"])
    assert report["human_summary"][-1] == (
        "Azione consigliata: correggere gli errori e ripetere il dry-run.")
    text = json.dumps(report).lower()
    for forbidden in ("password", "token", "base64", "file_bytes"):
        assert forbidden not in text


def test_pipeline_storage_failure_blocks_handoff_and_completion(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    failed = StorageStageResult(
        "att-1", "account_1", "missing.pdf", "", None, "a" * 64, 4,
        False, False, "staging_failed", "quarantine source file is missing",
    )
    runner = LocalPipelineRunner(
        accounts, paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log, (failed,)),
        handoff_factory=lambda: FakeHandoffPhase(log),
        completion_factory=lambda: FakePhase("completion", log),
    )

    result = runner.run(dry_run=False)

    assert result.status == "completed_with_errors"
    assert ("handoff", False) not in log
    assert ("completion", False) not in log
    assert any("staging_failed" in error for error in result.errors)


def test_missing_local_file_is_reacquired_staged_and_handed_off(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    environ = {
        "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
        "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
    }
    initial = MultiAccountImapProcessor(
        accounts, paths=paths, environ=environ,
        mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
        scanner=FakeScanner(ScanVerdict.CLEAN),
    ).process(dry_run=False)
    for item in initial:
        with sqlite3.connect(paths.state_db) as db:
            relative_path = db.execute(
                "SELECT relative_path FROM attachments WHERE attachment_id=?",
                (item.attachment_id,),
            ).fetchone()[0]
        (paths.root / relative_path).unlink()
    staging = (tmp_path / "staging").resolve()
    staging.mkdir()
    storage_config = LocalStorageConfig("local_filesystem", staging)
    delivered = []

    class CapturingHandoff:
        def deliver(self, storage_results, dry_run):
            delivered.extend(storage_results)
            return tuple(OperationalHandoffResult(
                item.attachment_id, item.account_alias, "created", "delivered"
            ) for item in storage_results)

    runner = LocalPipelineRunner(
        accounts, paths=paths,
        processor_factory=lambda: MultiAccountImapProcessor(
            accounts, paths=paths, environ=environ,
            mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
            scanner=FakeScanner(ScanVerdict.CLEAN),
        ),
        storage_factory=lambda: LocalFilesystemStorageAdapter(
            state_db=paths.state_db, local_data_root=paths.root, config=storage_config,
        ),
        handoff_factory=CapturingHandoff,
        completion_factory=lambda: FakePhase("completion", []),
    )

    result = runner.run(dry_run=False)

    assert result.status != "completed_with_errors"
    assert len(delivered) == 2
    assert all(item.status == "staged_storage" for item in delivered)
    assert all((staging / item.staged_path).is_file() for item in delivered)


def test_first_pipeline_cycle_reacquires_and_copies_after_local_reset(tmp_path):
    config_path = write_config(tmp_path / "config")
    accounts = load_multi_account_config(config_path)[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    paths.create()
    (paths.incoming / "obsolete.pdf").write_bytes(b"old")
    environ = {
        "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
        "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "synthetic-secret",
    }
    reset = reset_local_state(paths.root, backup=True, confirm=True)
    staging = (tmp_path / "staging").resolve()
    staging.mkdir()
    storage_config = LocalStorageConfig("local_filesystem", staging)

    runner = LocalPipelineRunner(
        accounts, paths=paths,
        processor_factory=lambda: MultiAccountImapProcessor(
            accounts, paths=paths, environ=environ,
            mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
            scanner=FakeScanner(ScanVerdict.CLEAN),
        ),
        storage_factory=lambda: LocalFilesystemStorageAdapter(
            state_db=paths.state_db, local_data_root=paths.root, config=storage_config,
        ),
        completion_factory=lambda: FakePhase("completion", []),
        config_path=config_path,
    )

    result = runner.run(dry_run=False)

    assert reset.backup_path is not None
    assert config_path.is_file()
    assert environ["VIRGILIO_IMAP_ACCOUNT_1_PASSWORD"] == "synthetic-secret"
    assert result.status != "completed_with_errors"
    staged_files = tuple(path for path in staging.rglob("*") if path.is_file())
    assert any(path.read_bytes() == b"%PDF" for path in staged_files)


def test_pipeline_handoff_runs_after_storage_and_before_completion(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    handoff_result = OperationalHandoffResult(
        attachment_id="att-1",
        account_alias="account_1",
        status="waiting",
        message="waiting",
    )
    runner = LocalPipelineRunner(
        accounts,
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        handoff_factory=lambda: FakeHandoffPhase(log, (handoff_result,)),
        completion_factory=lambda: FakePhase("completion", log),
    )

    result = runner.run(dry_run=False)

    assert log == [
        ("scan", False),
        ("process", False),
        ("storage", False),
        ("handoff", False),
        ("completion", False),
    ]
    assert result.status == "completed_with_warnings"
    assert any("waiting for Limbo synchronization" in item for item in result.warnings)


def test_pipeline_updates_registry_after_handoff_and_before_completion(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    runner = LocalPipelineRunner(
        accounts,
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        handoff_factory=lambda: FakeHandoffPhase(log),
        registry_export_factory=lambda: FakeRegistryPhase(
            log, FakeRegistryResult("completed")
        ),
        completion_factory=lambda: FakePhase("completion", log),
    )

    result = runner.run(dry_run=False)

    assert result.status == "completed_with_warnings"
    assert log == [
        ("scan", False),
        ("process", False),
        ("storage", False),
        ("handoff", False),
        ("registry", False),
        ("completion", False),
    ]


def test_pipeline_registry_failure_keeps_message_uncompleted_for_retry(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    log = []
    runner = LocalPipelineRunner(
        accounts,
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner_factory=lambda: FakePhase("scan", log),
        processor_factory=lambda: FakePhase("process", log),
        storage_factory=lambda: FakePhase("storage", log),
        registry_export_factory=lambda: FakeRegistryPhase(
            log,
            FakeRegistryResult(
                "completed_with_errors", ("synthetic registry failure",)
            ),
        ),
        completion_factory=lambda: FakePhase("completion", log),
    )

    result = runner.run(dry_run=False)

    assert result.status == "completed_with_errors"
    assert ("completion", False) not in log
    assert ("registry", False) in log
    assert any("Register update did not complete" in item for item in result.errors)


def test_run_local_pipeline_cli_invalid_config(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "run-local-pipeline",
        "--config", str(tmp_path / "missing.yaml"), "--dry-run",
    ])
    from virgilio_connector.__main__ import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def write_storage_and_bucoliche_config(tmp_path, storage_adapter="local_filesystem"):
    staging = tmp_path / "staging"; staging.mkdir(parents=True)
    path = write_config(tmp_path)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"""
storage:
  adapter: {storage_adapter}
  staging_dir: "{staging}"
  use_account_subfolders: true
  copy_manifest: true
  overwrite: false
  create_staging_dir: false
bucoliche:
  enabled: true
  adapter: google_sheets_append_only
  credentials_mode: user_oauth_local
""")
    return path


def test_storage_loader_does_not_read_bucoliche_adapter(tmp_path):
    config = write_storage_and_bucoliche_config(tmp_path)
    storage = load_storage_config(config)
    assert storage.adapter == "local_filesystem"


def test_storage_loader_rejects_bucoliche_adapter_in_storage_section(tmp_path):
    config = write_storage_and_bucoliche_config(tmp_path, "google_sheets_append_only")
    with pytest.raises(MultiAccountConfigError, match="unsupported storage adapter"):
        load_storage_config(config)


def test_pipeline_cli_dry_run_keeps_storage_and_bucoliche_separate(tmp_path, monkeypatch, capsys):
    config = write_storage_and_bucoliche_config(tmp_path)
    log = []
    import virgilio_connector.cli as cli
    monkeypatch.setattr(cli, "MultiAccountReadonlyScanner",
                        lambda *a, **k: FakePhase("scan", log))
    monkeypatch.setattr(cli, "MultiAccountImapProcessor",
                        lambda *a, **k: FakePhase("process", log))
    monkeypatch.setattr(cli, "LocalFilesystemStorageAdapter",
                        lambda *a, **k: FakePhase("storage", log))
    monkeypatch.setattr(cli, "LocalCompletionRunner",
                        lambda *a, **k: FakePhase("completion", log))
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(tmp_path / ".local_data"))
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "run-local-pipeline",
                                      "--config", str(config), "--dry-run"])
    assert cli.main() == 0
    assert log == [("scan", True), ("process", True), ("storage", True),
                   ("completion", True)]
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
    assert (tmp_path / ".local_data" / "state.db").is_file()


def test_pipeline_cli_human_output_uses_summary(tmp_path, monkeypatch, capsys):
    config = write_storage_and_bucoliche_config(tmp_path)
    log = []
    import virgilio_connector.cli as cli
    monkeypatch.setattr(cli, "MultiAccountReadonlyScanner",
                        lambda *a, **k: FakePhase("scan", log))
    monkeypatch.setattr(cli, "MultiAccountImapProcessor",
                        lambda *a, **k: FakePhase("process", log))
    monkeypatch.setattr(cli, "LocalFilesystemStorageAdapter",
                        lambda *a, **k: FakePhase("storage", log))
    monkeypatch.setattr(cli, "LocalCompletionRunner",
                        lambda *a, **k: FakePhase("completion", log))
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(tmp_path / ".local_data"))
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "run-local-pipeline",
                                      "--config", str(config), "--dry-run", "--human"])
    assert cli.main() == 0
    text = capsys.readouterr().out
    assert "Esito pipeline: completed_with_warnings (dry-run)" in text
    assert '"dry_run"' not in text


class FakeDoctorMailbox:
    instances = []

    def __init__(self, config, fail=False):
        self.config = config
        self.fail = fail
        self.calls = []
        self.__class__.instances.append(self)

    def list_pending(self):
        self.calls.append(("select_readonly", self.config.mailbox))
        if self.fail:
            raise RuntimeError("imap down")
        return ()


class FakeUnavailableScanner:
    @property
    def available(self):
        return False


def doctor_config(tmp_path, staging):
    return write_storage_config(tmp_path, staging)


def test_doctor_ready_with_scanner_warning(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    accounts = load_multi_account_config(doctor_config(tmp_path, staging))[:1]
    result = LocalDoctor(
        accounts,
        storage=load_storage_config(doctor_config(tmp_path, staging)),
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner=FakeUnavailableScanner(),
        environ={
            "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
        },
        mailbox_factory=lambda config: FakeDoctorMailbox(config),
    ).run()
    assert result.status == "READY_WITH_WARNINGS"
    assert result.accounts[0]["username_env"] == "OK"
    assert result.accounts[0]["password_env"] == "OK"
    assert "secret" not in result.to_json()
    assert any("scanner locale" in item for item in result.suggested_fixes)


def test_doctor_missing_config_cli_blocked(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [
        "python -m virgilio_connector", "doctor",
        "--config", str(tmp_path / "missing.yaml"),
    ])
    from virgilio_connector.__main__ import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.err or captured.out)
    assert payload["status"] == "BLOCKED"
    assert payload["suggested_fixes"] == [
        "Correggi il file di configurazione locale e riesegui il doctor."
    ]


def test_doctor_duplicate_alias_blocked(tmp_path):
    path = tmp_path / "dup.yaml"
    path.write_text("""accounts:
  - account_alias: same_alias
    email: a@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_A_USERNAME
    password_env: VIRGILIO_A_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
  - account_alias: same_alias
    email: b@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_B_USERNAME
    password_env: VIRGILIO_B_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
storage:
  adapter: local_filesystem
  staging_dir: "C:\\Temp"
""", encoding="utf-8")
    with pytest.raises(MultiAccountConfigError):
        load_multi_account_config(path)


def test_doctor_env_and_storage_missing_blocked(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    result = LocalDoctor(
        accounts,
        storage=LocalStorageConfig("local_filesystem", tmp_path / "missing"),
        paths=LocalDataPaths(tmp_path / ".local_data"),
        scanner=FakeUnavailableScanner(),
        environ={},
        mailbox_factory=lambda config: FakeDoctorMailbox(config),
    ).run()
    assert result.status == "BLOCKED"
    assert any("username_env missing" in item for item in result.errors)
    assert any("staging_dir does not exist" in item for item in result.errors)
    assert any("variabili ambiente IMAP" in item for item in result.suggested_fixes)
    assert any("storage.staging_dir" in item for item in result.suggested_fixes)


def test_doctor_imap_error_does_not_block_other_account(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    accounts = (
        LocalImapAccount("a_box", "a@example.invalid", "generic", "imap.example.invalid", 993,
                         "A_USER", "A_PASS", "INBOX", "done", "err"),
        LocalImapAccount("b_box", "b@example.invalid", "generic", "imap.example.invalid", 993,
                         "B_USER", "B_PASS", "INBOX", "done", "err"),
    )
    result = LocalDoctor(
        accounts, storage=LocalStorageConfig("local_filesystem", staging),
        paths=LocalDataPaths(tmp_path / ".local_data"), scanner=FakeUnavailableScanner(),
        environ={"A_USER": "a", "A_PASS": "a", "B_USER": "b", "B_PASS": "b"},
        mailbox_factory=lambda config: FakeDoctorMailbox(config, fail=config.username == "a"),
    ).run()
    assert result.status == "BLOCKED"
    assert [row["imap"] for row in result.accounts] == ["ERROR", "OK_READONLY"]
    calls = [str(call).upper() for inst in FakeDoctorMailbox.instances for call in inst.calls]
    for forbidden in ("STORE", "COPY", "MOVE", "DELETE", "EXPUNGE"):
        assert not any(forbidden in call for call in calls)
    assert any("input_folder" in item for item in result.suggested_fixes)


def test_doctor_cli_human_output_shows_actions(tmp_path, monkeypatch, capsys):
    staging = tmp_path / "staging"
    staging.mkdir()
    config = doctor_config(tmp_path, staging)
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(tmp_path / "local-data"))
    monkeypatch.setenv("VIRGILIO_IMAP_ACCOUNT_1_USERNAME", "user@example.invalid")
    monkeypatch.setenv("VIRGILIO_IMAP_ACCOUNT_1_PASSWORD", "secret")
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "doctor", "--config", str(config), "--human",
    ])
    import virgilio_connector.cli as cli
    monkeypatch.setattr(cli, "select_scanner", lambda *_: FakeUnavailableScanner())
    monkeypatch.setattr(cli, "LocalDoctor", lambda *args, **kwargs: LocalDoctor(
        *args,
        **kwargs,
        mailbox_factory=lambda config: FakeDoctorMailbox(config),
    ))

    assert cli.main() == 0
    text = capsys.readouterr().out
    assert "Esito doctor: READY_WITH_WARNINGS" in text
    assert "Azione consigliata:" in text
    assert '"status"' not in text
