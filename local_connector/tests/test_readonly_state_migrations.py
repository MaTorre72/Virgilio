import sqlite3

from virgilio_connector.completion import LocalCompletionRunner
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.multi_account import LocalImapAccount, LocalStorageConfig
from virgilio_connector.pipeline import LocalPipelineRunner
from virgilio_connector.readonly_state import ensure_state_db
from virgilio_connector.storage_adapter import LocalFilesystemStorageAdapter


class EmptyPhase:
    def scan(self, dry_run): return ()
    def process(self, dry_run): return ()


def account():
    return LocalImapAccount("test_box", "test@example.invalid", "generic",
        "imap.example.invalid", 993, "TEST_USER", "TEST_PASS", "INBOX", "done", "error")


def pipeline(root, staging):
    paths = LocalDataPaths(root)
    storage = LocalStorageConfig("local_filesystem", staging)
    return LocalPipelineRunner((account(),), paths=paths,
        scanner_factory=lambda: EmptyPhase(), processor_factory=lambda: EmptyPhase(),
        storage_factory=lambda: LocalFilesystemStorageAdapter(state_db=paths.state_db,
            local_data_root=paths.root, config=storage),
        completion_factory=lambda: LocalCompletionRunner((account(),), paths=paths))


def test_ensure_state_db_creates_and_is_idempotent(tmp_path):
    root = tmp_path / ".local_data"
    path, warnings = ensure_state_db(root)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO runs(started_at,dry_run,status) VALUES('now',0,'completed')")
        db.commit()
    second, _ = ensure_state_db(root)
    with sqlite3.connect(second) as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
    assert path == second and warnings == ()


def test_pipeline_dry_run_initializes_missing_db_and_skips_empty_phases(tmp_path):
    root = tmp_path / ".local_data"; staging = tmp_path / "staging"; staging.mkdir()
    result = pipeline(root, staging).run(dry_run=True)
    assert (root / "state.db").is_file()
    assert result.status == "completed_with_warnings" and result.errors == ()
    assert "storage: skipped_no_ready_attachments" in result.warnings
    assert "completion: skipped_no_staged_messages" in result.warnings


def test_empty_existing_local_data_is_initialized(tmp_path):
    root = tmp_path / ".local_data"; root.mkdir()
    staging = tmp_path / "staging"; staging.mkdir()
    assert pipeline(root, staging).run(dry_run=True).status == "completed_with_warnings"
    assert (root / "state.db").is_file()


def test_legacy_schema_is_additively_migrated_and_pipeline_runs(tmp_path):
    root = tmp_path / ".local_data"; root.mkdir(); db_path = root / "state.db"
    with sqlite3.connect(db_path) as db:
        db.executescript("""CREATE TABLE runs(id INTEGER PRIMARY KEY);
            CREATE TABLE messages(id INTEGER PRIMARY KEY);
            CREATE TABLE attachments(id INTEGER PRIMARY KEY);
            INSERT INTO attachments(id) VALUES(1);""")
    _, warnings = ensure_state_db(root)
    staging = tmp_path / "staging"; staging.mkdir()
    result = pipeline(root, staging).run(dry_run=True)
    with sqlite3.connect(db_path) as db:
        message_columns = {row[1] for row in db.execute("PRAGMA table_info(messages)")}
        attachment_columns = {row[1] for row in db.execute("PRAGMA table_info(attachments)")}
    assert {"account_alias", "message_state", "fingerprint"} <= message_columns
    assert {"attachment_id", "source_message_id", "staged_manifest_path"} <= attachment_columns
    assert warnings and warnings[0].startswith("legacy_incomplete")
    assert result.errors == ()


def test_storage_and_completion_on_empty_db_return_empty(tmp_path):
    root = tmp_path / ".local_data"; staging = tmp_path / "staging"; staging.mkdir()
    paths = LocalDataPaths(root)
    storage = LocalFilesystemStorageAdapter(state_db=paths.state_db,
        local_data_root=root, config=LocalStorageConfig("local_filesystem", staging))
    assert storage.stage_ready(dry_run=True) == ()
    assert LocalCompletionRunner((account(),), paths=paths).complete(dry_run=True) == ()
