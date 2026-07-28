from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_bootstrap_uses_the_declared_development_extra() -> None:
    script = (ROOT / "scripts/dev/bootstrap_local_connector.ps1").read_text(
        encoding="utf-8"
    )

    assert 'pip install -e "$ConnectorRoot[dev]"' in script
    assert "requirements" not in script
    assert "pip install pytest" not in script


def test_current_runbook_exposes_one_fresh_clone_path() -> None:
    runbook = (ROOT / "docs/RUNBOOKS.md").read_text(encoding="utf-8")

    assert "bootstrap_local_connector.ps1" in runbook
    assert "git clone" in runbook
    assert "smoke_local_connector.ps1" in runbook
