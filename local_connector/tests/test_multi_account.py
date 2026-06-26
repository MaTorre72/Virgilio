from pathlib import Path
import sqlite3
import json
import sys

import pytest

from virgilio_connector.imap_readonly import DetectedAttachment
from virgilio_connector.completion import LocalCompletionRunner
from virgilio_connector.multi_account import (
    LocalImapAccount,
    MultiAccountImapProcessor,
    MultiAccountConfigError,
    MultiAccountReadonlyScanner,
    LocalStorageConfig,
    load_storage_config,
    load_multi_account_config,
)
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.ports import MessageReference
from virgilio_connector.scanner import LocalScanResult, ScanVerdict
from virgilio_connector.storage_adapter import (
    LocalFilesystemStorageAdapter,
    StorageAdapterError,
)


def write_config(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "accounts.yaml"
    path.write_text("""accounts:
  - account_alias: marco_sigmapiu
    email: marco@example.invalid
    provider_hint: gmail_workspace
    imap_host: imap.gmail.com
    imap_port: 993
    username_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME
    password_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD
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

    def __init__(self, account, *, input_present=True, done_present=False, fail=False):
        self.account = account
        self.input_present = input_present
        self.done_present = done_present
        self.fail = fail
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
            raise RuntimeError("ack boom")


def test_loads_multi_account_yaml_without_secret_values(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    assert [account.account_alias for account in accounts] == ["marco_sigmapiu", "disabled_box"]
    assert accounts[0].email == "marco@example.invalid"
    assert accounts[0].max_messages == 7
    assert accounts[0].password_env == "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD"


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
        account_alias="marco_sigmapiu",
        email="marco@example.invalid",
        provider_hint="gmail_workspace",
        imap_host="imap.gmail.com",
        imap_port=993,
        username_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME",
        password_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD",
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
    assert "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME" in result[0].error
    assert calls == []


def test_dry_run_scans_enabled_accounts_without_writing_state(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=True)
    assert [(item.account_alias, item.status, item.messages_seen) for item in result] == [
        ("marco_sigmapiu", "ok", 2),
        ("disabled_box", "disabled", 0),
    ]
    assert not paths.root.exists()
    assert len(FakeMailbox.instances) == 1
    assert FakeMailbox.instances[0].config.password == "secret"


def test_non_dry_run_records_account_alias_separately(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=False)
    assert result[0].status == "ok"
    with sqlite3.connect(paths.state_db) as db:
        runs = db.execute("SELECT account_alias,messages_seen,attachments_seen,status FROM runs").fetchall()
        messages = db.execute("SELECT account_alias,message_uid,mailbox FROM messages ORDER BY message_uid").fetchall()
        attachments = db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    assert runs == [("marco_sigmapiu", 2, 0, "completed")]
    assert messages == [
        ("marco_sigmapiu", "41", "Virgilio/da-traghettare"),
        ("marco_sigmapiu", "42", "Virgilio/da-traghettare"),
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
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeProcessMailbox(config, root),
        scanner=scanner,
    ).process(dry_run=dry_run)
    return result, paths


def test_process_dry_run_lists_candidate_attachments_without_files_or_db(tmp_path):
    result, paths = process(tmp_path, dry_run=True)
    assert len(result) == 2
    assert result[0].account_alias == "marco_sigmapiu"
    assert result[0].original_filename == "report.pdf"
    assert result[0].quarantine_status == "quarantined_unverified"
    assert result[0].saved is False
    assert not paths.root.exists()


def test_process_writes_quarantine_manifest_and_sqlite_per_account(tmp_path):
    result, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    assert result[0].quarantine_status == "ready_for_caronte"
    assert result[0].saved is True
    assert result[0].manifest_path
    manifest_path = paths.root / result[0].manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["connector_type"] == "local_imap"
    assert manifest["account_alias"] == "marco_sigmapiu"
    assert manifest["source_email"] == "marco@example.invalid"
    assert manifest["source_message_uid"] == "41"
    assert manifest["source_message_id"] == "<a@example.invalid>"
    assert manifest["attachment_id"] == result[0].attachment_id
    assert manifest["sha256"] == result[0].sha256
    assert manifest["scan_engine"] == "fake"
    assert manifest["scan_result"] == "clean"
    assert len(list((paths.root / "accounts" / "marco_sigmapiu" / "quarantine" / "ready").rglob("*.pdf"))) == 2
    with sqlite3.connect(paths.state_db) as db:
        rows = db.execute("""SELECT a.account_alias,a.attachment_id,a.source_email,
            a.status,a.manifest_path,m.message_uid,m.message_id,m.subject
            FROM attachments a JOIN messages m ON m.id=a.message_id
            ORDER BY m.message_uid""").fetchall()
    assert rows[0][0] == "marco_sigmapiu"
    assert rows[0][2] == "marco@example.invalid"
    assert rows[0][3] == "ready_for_caronte"
    assert rows[0][4] == result[0].manifest_path
    assert rows[0][5:] == ("41", "<a@example.invalid>", "Subject A")


def test_process_is_idempotent_for_same_attachment_id_and_sha(tmp_path):
    result1, paths = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    result2, _ = process(tmp_path, scanner=FakeScanner(ScanVerdict.CLEAN))
    assert result2[0].attachment_id == result1[0].attachment_id
    assert result2[0].saved is False
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2


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
    assert len(list((paths.root / "accounts" / "marco_sigmapiu" / "quarantine" / "rejected").rglob("*.pdf"))) == 2
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
    assert manifest["account_alias"] == "marco_sigmapiu"
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
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=mailbox_factory or (lambda account: FakeAckMailbox(account)),
    ).complete(dry_run=dry_run)


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


def test_completion_real_ack_updates_sqlite_and_report(tmp_path):
    accounts, paths = staged_fixture(tmp_path)
    FakeAckMailbox.instances.clear()
    result = complete(paths, accounts)
    assert result[0].status == "completed"
    assert result[0].report_path
    assert FakeAckMailbox.instances[0].calls == [
        ("input_contains_uid", "marco_sigmapiu", "41"),
        ("add_done_label_only", "marco_sigmapiu", "Virgilio/traghettate", "41"),
    ]
    all_calls = [str(call).upper() for inst in FakeAckMailbox.instances for call in inst.calls]
    for forbidden in ("EXPUNGE", "STORE", "DELETE", "MOVE", "SEEN"):
        assert not any(forbidden in call for call in all_calls)
    report = json.loads((paths.root / result[0].report_path).read_text(encoding="utf-8"))
    assert report["messages_completed"] == 2
    assert report["results"][0]["account_alias"] == "marco_sigmapiu"
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
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT message_state FROM messages WHERE id=1").fetchone()[0] == "completed"


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
             "accounts/marco_sigmapiu/quarantine/ready/41/001-report.pdf", "test", "now"))
        db.commit()
    second = LocalImapAccount(
        account_alias="second_box", email="second@example.invalid",
        provider_hint="generic", imap_host="imap.example.invalid", imap_port=993,
        username_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME",
        password_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD",
        input_folder="INBOX", done_folder="done", error_folder="error",
        ack_enabled=True, ack_strategy="add_done_label_only",
    )
    results = complete(paths, (accounts[0], second),
        mailbox_factory=lambda account: FakeAckMailbox(account, fail=account.account_alias == "marco_sigmapiu"))
    statuses = {item.account_alias: item.status for item in results}
    assert statuses["marco_sigmapiu"] == "ack_failed"
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
