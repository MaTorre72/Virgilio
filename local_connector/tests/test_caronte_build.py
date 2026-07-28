from __future__ import annotations

from pathlib import Path
import sys
import tomllib

import virgilio_connector
from virgilio_connector import build_entry
from virgilio_connector.application.operation_runner import _runtime_command


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


def test_product_version_has_one_authoritative_package_value() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    release_marker = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    build_text = (REPO_ROOT / "scripts" / "dev" / "build_caronte.ps1").read_text(encoding="utf-8")

    assert release_marker == virgilio_connector.__version__ == "1.1.0"
    assert project["project"]["dynamic"] == ["version"]
    assert project["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "virgilio_connector._version.__version__"
    }
    assert "_version.py" in build_text


def test_build_configuration_defines_one_folder_caronte() -> None:
    spec = (ROOT / "build" / "Caronte.spec").read_text(encoding="utf-8")

    assert 'name="Caronte"' in spec
    assert "COLLECT(" in spec
    assert "console=False" in spec
    assert "Path(SPECPATH).parent" in spec
    assert '"resources"' in spec
    assert "google_oauth_client.json" in spec
    build_script = REPO_ROOT / "scripts" / "dev" / "build_caronte.ps1"
    assert build_script.is_file()
    build_text = build_script.read_text(encoding="utf-8")
    assert "import tkinter" in build_text
    assert "SOURCE_DATE_EPOCH" in build_text
    assert "PYTHONHASHSEED" in build_text
    assert "GoogleOAuthClientPath" in build_text
    assert "CARONTE_GOOGLE_OAUTH_CLIENT_PATH" in build_text
    assert "HumanAcceptanceBuild" in build_text
    assert '"dirty"' in build_text
    assert '"codex/v1.1-development"' in build_text
    assert "build_manifest.json" in build_text
    assert "pyinstaller_version" in build_text
    assert "build_id" in build_text
    assert "oauth_client_included" in build_text
    assert "CARONTE_BUILD_MANIFEST_PATH" in spec
    assert (REPO_ROOT / "scripts" / "dev" / "smoke_caronte_build.ps1").is_file()
    assert (REPO_ROOT / "docs" / "RUNBOOKS.md").is_file()


def test_windows_timezone_data_is_declared_for_standalone_runtime() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert any(item.startswith("tzdata>=") for item in project["project"]["dependencies"])


def test_build_entry_opens_user_application_without_arguments(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(sys, "argv", ["Caronte.exe"])
    monkeypatch.setattr(
        "virgilio_connector.user_app.launch_user_app",
        lambda: called.append("Caronte") or 0,
    )

    assert build_entry.main() == 0
    assert called == ["Caronte"]


def test_build_entry_opens_requested_isolated_demo_screen(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(
        sys, "argv", ["Caronte.exe", "--demo", "--demo-screen=home", "--demo-scale=1.25"]
    )
    monkeypatch.setattr(
        "virgilio_connector.user_app.launch_user_app",
        lambda **kwargs: called.append(kwargs) or 0,
    )

    assert build_entry.main() == 0
    assert called == [{"demo": True, "demo_screen": "home", "demo_scale": 1.25}]


def test_frozen_worker_reuses_bundled_executable(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\Caronte\Caronte.exe")

    assert _runtime_command(["scan-imap-accounts", "--config", "config.yaml"]) == [
        r"C:\Program Files\Caronte\Caronte.exe",
        "scan-imap-accounts",
        "--config",
        "config.yaml",
    ]


def test_development_worker_keeps_module_command(monkeypatch) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Python\python.exe")

    assert _runtime_command(["watch"]) == [
        r"C:\Python\python.exe",
        "-m",
        "virgilio_connector",
        "watch",
    ]
