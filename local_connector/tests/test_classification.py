from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from virgilio_connector.classification import (AttachmentClassificationProposer,
                                               ClassificationProposalError)
from virgilio_connector.litellm_gateway import LiteLLMGatewayConfig


def _write_manifest(path: Path, *, subject: str = "Invoice June", filename: str = "invoice-2026.pdf") -> Path:
    path.write_text(json.dumps({
        "attachment_id": "att-123",
        "account_alias": "demo_box",
        "subject": subject,
        "original_filename": filename,
        "file_extension": Path(filename).suffix.lower(),
        "mime_type": "application/pdf",
        "source_sender": "billing@example.invalid",
        "source_mailbox": "Virgilio/da-traghettare",
        "scan_result": "clean",
        "status_reason": "fake clean",
    }, ensure_ascii=False), encoding="utf-8")
    return path


def test_classification_proposal_uses_manifest_metadata(tmp_path):
    manifest = _write_manifest(tmp_path / "invoice.manifest.json")
    result = AttachmentClassificationProposer(LiteLLMGatewayConfig(
        max_total_tokens=500,
        max_output_tokens=80,
        max_cost_eur=0.1,
    )).propose_from_manifest(manifest)
    assert result.dry_run is True
    assert result.review_required is True
    assert result.status == "proposal_only"
    assert result.proposed_classification == "amministrazione_fattura"
    assert result.confidence == "medium"
    assert "mock_provider_only" in result.warnings
    assert "human_review_required" in result.warnings
    assert any("scan result: clean" == item for item in result.reasons)


def test_classification_proposal_falls_back_to_generic_review_queue(tmp_path):
    manifest = _write_manifest(
        tmp_path / "generic.manifest.json",
        subject="Documentazione allegata",
        filename="allegato.pdf",
    )
    result = AttachmentClassificationProposer(LiteLLMGatewayConfig(
        max_total_tokens=500,
        max_output_tokens=80,
        max_cost_eur=0.1,
    )).propose_from_manifest(manifest)
    assert result.proposed_classification == "documento_generico_da_rivedere"
    assert result.confidence == "low"
    assert any("generic review queue" in item for item in result.reasons)


def test_classification_proposal_rejects_invalid_manifest(tmp_path):
    manifest = tmp_path / "broken.manifest.json"
    manifest.write_text("[]", encoding="utf-8")
    with pytest.raises(ClassificationProposalError, match="manifest must be a JSON object"):
        AttachmentClassificationProposer(LiteLLMGatewayConfig(max_cost_eur=0.1)).propose_from_manifest(manifest)


def test_cli_classify_manifest_dry_run_returns_json(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    manifest = _write_manifest(tmp_path / "invoice.manifest.json")
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "classify-manifest-dry-run",
        "--manifest", str(manifest),
        "--budget-tokens", "600",
        "--max-cost-eur", "0.02",
    ])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["review_required"] is True
    assert payload["proposed_classification"] == "amministrazione_fattura"


def test_cli_classify_manifest_dry_run_human_summary(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    manifest = _write_manifest(tmp_path / "minutes.manifest.json", subject="Meeting minutes", filename="minutes.docx")
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "classify-manifest-dry-run",
        "--manifest", str(manifest),
        "--human",
    ])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Proposta classificazione: riunione_verbale" in output
    assert "Revisione umana obbligatoria: si" in output
