from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from virgilio_connector import build_entry
from virgilio_connector.build_info import BuildInfoError, build_info_json, load_build_info
from virgilio_connector.user_app.about import ABOUT_TITLE, visible_build_information


def manifest_values() -> dict[str, str]:
    return {
        "product_name": "Caronte",
        "version": "1.1.0",
        "git_commit": "a1b2c3d4e5f67890123456789012345678901234",
        "git_short_commit": "a1b2c3d",
        "build_utc": "2026-07-20T17:00:00Z",
        "source_branch": "codex/v1.1-development",
        "working_tree": "clean",
        "python_version": "3.13.5",
        "pyinstaller_version": "6.21.0",
        "build_id": "12345678-1234-4abc-8def-1234567890ab",
    }


def write_manifest(path: Path, values: dict[str, str] | None = None) -> Path:
    path.write_text(json.dumps(values or manifest_values()), encoding="utf-8")
    return path


def test_manifest_loads_all_required_build_identity_fields(tmp_path: Path) -> None:
    info = load_build_info(write_manifest(tmp_path / "build_manifest.json"))

    assert info.product_name == "Caronte"
    assert info.git_commit.startswith(info.git_short_commit)
    assert info.source_branch == "codex/v1.1-development"
    assert info.working_tree == "clean"
    assert info.python_version == "3.13.5"
    assert info.pyinstaller_version == "6.21.0"


@pytest.mark.parametrize(
    ("field", "value"),
    (("git_commit", "missing"), ("working_tree", "unknown"), ("build_id", "not-a-uuid"), ("build_utc", "today")),
)
def test_manifest_rejects_invalid_identity(tmp_path: Path, field: str, value: str) -> None:
    values = manifest_values()
    values[field] = value

    with pytest.raises(BuildInfoError):
        load_build_info(write_manifest(tmp_path / "invalid.json", values))


def test_build_info_command_and_about_use_exactly_the_same_public_values(monkeypatch, capsys, tmp_path: Path) -> None:
    info = load_build_info(write_manifest(tmp_path / "build_manifest.json"))
    monkeypatch.setattr(sys, "argv", ["Caronte.exe", "--build-info"])
    monkeypatch.setattr(build_entry, "load_build_info", lambda: info)

    assert build_entry.main() == 0
    command_values = json.loads(capsys.readouterr().out)
    about_values = dict(visible_build_information(info))

    assert command_values == json.loads(build_info_json(info))
    assert about_values == {
        "Versione": command_values["version"],
        "Commit": command_values["commit"],
        "Data della build": command_values["build_utc"],
        "Build ID": command_values["build_id"],
    }
    assert ABOUT_TITLE == "Informazioni su Caronte"
    assert command_values["version"] == "1.1.0"


def test_build_info_command_fails_without_a_valid_manifest(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["Caronte.exe", "--build-info"])
    monkeypatch.setattr(build_entry, "load_build_info", lambda: (_ for _ in ()).throw(BuildInfoError("missing")))

    assert build_entry.main() != 0
    assert "assenti o non valide" in capsys.readouterr().err


def test_about_information_exposes_no_build_environment_details(tmp_path: Path) -> None:
    visible = " ".join(value for _, value in visible_build_information(load_build_info(write_manifest(tmp_path / "build_manifest.json")))).lower()

    assert all(term not in visible for term in ("python", "repository", "env", "c:\\", "users\\"))
