import ast
import json
from pathlib import Path
from tkinter import Tk

from virgilio_connector.application.maintenance import MaintenanceService
from virgilio_connector.application.credentials import FakeCredentialStore
from virgilio_connector.application.operational_connection import (
    CONNECTION_CREDENTIAL,
    OperationalConnectionService,
)
from virgilio_connector.application.registry_configuration import RegistryConfigurationService
from virgilio_connector.maintenance_gui import (
    MAINTENANCE_OPERATIONS,
    WINDOW_TITLE,
    MaintenanceApp,
)
from virgilio_connector.state_db import StateStore


class FakeRoot:
    def title(self, value):
        self.window_title = value

    def minsize(self, width, height):
        self.minimum_size = (width, height)


class FakeWidget:
    created = []

    def __init__(self, parent, **kwargs):
        self.kwargs = kwargs
        self.config = dict(kwargs)
        self.states = set()
        type(self).created.append(self)

    def grid(self, **kwargs):
        self.grid_options = kwargs

    def configure(self, **kwargs):
        self.config.update(kwargs)

    def state(self, states):
        for value in states:
            if value.startswith("!"):
                self.states.discard(value[1:])
            else:
                self.states.add(value)


class FakeFrame(FakeWidget):
    created = []


class FakeLabel(FakeWidget):
    created = []


class FakeButton(FakeWidget):
    created = []


class FakeEntry(FakeWidget):
    created = []

    def get(self):
        return self.config.get("value", "")

    def insert(self, index, value):
        self.config["value"] = value

    def delete(self, start, end=None):
        self.config["value"] = ""


class FakeTtk:
    Frame = FakeFrame
    Label = FakeLabel
    Button = FakeButton
    Checkbutton = FakeButton
    Entry = FakeEntry


def seed_data(root: Path) -> None:
    (root / "quarantine" / "incoming").mkdir(parents=True)
    (root / "quarantine" / "incoming" / "document.txt").write_text(
        "synthetic", encoding="utf-8"
    )
    (root / "machine_id").write_text("machine-test\n", encoding="utf-8")


def test_backup_copies_directory_and_content(tmp_path):
    root = tmp_path / "data"
    seed_data(root)

    result = MaintenanceService(root).create_backup()

    assert result.status == "completed"
    assert result.backup_path is not None
    assert result.files_copied == 2
    assert (result.backup_path / "quarantine" / "incoming" / "document.txt").read_text(
        encoding="utf-8"
    ) == "synthetic"
    assert (root / "quarantine" / "incoming" / "document.txt").is_file()


def test_integrity_reports_valid_and_corrupt_synthetic_databases(tmp_path):
    valid_root = tmp_path / "valid"
    StateStore(valid_root / "state.db").initialize()
    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / "state.db").write_bytes(b"not a sqlite database")

    assert MaintenanceService(valid_root).verify_integrity().status == "valid"
    assert MaintenanceService(corrupt_root).verify_integrity().status == "corrupt"


def test_diagnostic_report_has_minimum_content_and_redacts(tmp_path):
    root = tmp_path / "data"
    secret = "synthetic-secret"
    service = MaintenanceService(
        root,
        details_provider=lambda: {
            "mode": "test",
            "password": secret,
            "note": f"value={secret}",
        },
        redact=lambda value: value.replace(secret, "<redacted>"),
    )

    result = service.create_diagnostic_report()
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload)

    assert payload["application"] == "Caronte Manutenzione"
    assert payload["generated_at"]
    assert payload["integrity"]["status"] == "missing"
    assert payload["details"]["mode"] == "test"
    assert secret not in serialized
    assert payload["details"]["password"] == "<redacted>"


def test_reset_requires_confirmation_and_creates_backup(tmp_path):
    root = tmp_path / "data"
    seed_data(root)
    service = MaintenanceService(root)

    cancelled = service.reset(confirmed=False)
    assert cancelled.status == "cancelled"
    assert (root / "quarantine" / "incoming" / "document.txt").is_file()

    completed = service.reset(confirmed=True)
    assert completed.status == "completed"
    assert completed.backup_path is not None
    assert (completed.backup_path / "quarantine" / "incoming" / "document.txt").is_file()
    assert not (root / "quarantine" / "incoming" / "document.txt").exists()


def test_new_maintenance_presentation_has_only_supported_operations_and_no_legacy_import(tmp_path):
    root = FakeRoot()
    app = MaintenanceApp(root, MaintenanceService(tmp_path / "data"), ttk_module=FakeTtk)
    source = Path(__file__).parents[1] / "src" / "virgilio_connector" / "maintenance_gui.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imports = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert root.window_title == WINDOW_TITLE == "Caronte Manutenzione"
    assert root.minimum_size == (680, 420)
    assert MAINTENANCE_OPERATIONS == (
        "Registro condiviso", "Backup locale", "Verifica integrita`", "Report diagnostico",
        "Reset protetto",
    )
    assert all("gui" not in imported for imported in imports)
    assert app.reset().status == "cancelled"
    app.toggle_reset_confirmation()
    assert "selected" in app.confirm_control.states


def test_maintenance_explains_and_persists_all_virgilio_services(tmp_path):
    root = FakeRoot()
    path = tmp_path / "accounts.yaml"
    registry = RegistryConfigurationService(path)
    credentials = FakeCredentialStore()
    connection = OperationalConnectionService(path, credentials)
    app = MaintenanceApp(
        root, MaintenanceService(tmp_path / "data"), ttk_module=FakeTtk,
        registry_configuration=registry,
        operational_connection=connection,
    )
    app.registry_entry.insert(
        0, "https://docs.google.com/spreadsheets/d/abcDEFGhijklmNOPQRST_uvwx/edit"
    )
    app.connection_endpoint.insert(
        0, "https://script.google.com/macros/s/deployment/exec"
    )
    app.connection_code.insert(0, "protected-code")

    result = app.save_services()

    assert result is not None and result.configured
    assert registry.load().spreadsheet_id == "abcDEFGhijklmNOPQRST_uvwx"
    assert connection.load().configured
    assert credentials.read(CONNECTION_CREDENTIAL) == "protected-code"
    assert app.connection_code.get() == ""
    assert "protected-code" not in path.read_text(encoding="utf-8")
    visible = " ".join(
        widget.kwargs.get("text", "")
        for kind in (FakeLabel, FakeButton)
        for widget in kind.created
    )
    assert "Google Fogli" in visible
    assert "Gestisci deployment" in visible
    assert "VIRGILIO_TOKEN" in visible
    assert "protetta da Windows" in visible


def test_maintenance_configuration_fits_supported_window_and_scales(tmp_path):
    path = tmp_path / "accounts.yaml"
    root = Tk()
    root.withdraw()
    try:
        root.geometry("960x640")
        MaintenanceApp(
            root,
            MaintenanceService(tmp_path / "data"),
            registry_configuration=RegistryConfigurationService(path),
            operational_connection=OperationalConnectionService(
                path, FakeCredentialStore()
            ),
        )
        for scale in (1.0, 1.25):
            root.tk.call("tk", "scaling", scale)
            root.update_idletasks()
            assert root.winfo_reqwidth() <= 960
            assert root.winfo_reqheight() <= 640
    finally:
        root.destroy()
