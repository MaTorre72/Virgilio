"""Dry-run attachment classification proposals based on local manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from .litellm_gateway import LiteLLMGateway, LiteLLMGatewayConfig, LiteLLMRequest
from .policy import AttachmentPolicy, PolicyDecision


class ClassificationProposalError(RuntimeError):
    """Raised when a local manifest cannot be classified safely."""


@dataclass(frozen=True, slots=True)
class ClassificationProposal:
    manifest_path: str
    attachment_id: str
    account_alias: str
    dry_run: bool
    review_required: bool
    status: str
    proposed_classification: str
    confidence: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    llm_output_text: str
    llm_provider: str
    llm_model: str
    llm_total_tokens: int
    llm_estimated_cost_eur: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClassificationReview:
    manifest_path: str
    attachment_id: str
    account_alias: str
    dry_run: bool
    status: str
    proposed_classification: str
    reviewer: str
    decision: str
    review_completed: bool
    approved_for_future_flow: bool
    review_notes: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AttachmentClassificationProposer:
    def __init__(self, config: LiteLLMGatewayConfig, *,
                 gateway: LiteLLMGateway | None = None,
                 policy: AttachmentPolicy | None = None) -> None:
        self.config = config
        self.gateway = gateway or LiteLLMGateway(config)
        self.policy = policy or AttachmentPolicy()

    def propose_from_manifest(self, manifest_path: str | Path) -> ClassificationProposal:
        path = Path(manifest_path)
        manifest = _load_manifest(path)
        proposed_classification, confidence, reasons = self._heuristic_classification(manifest)
        response = self.gateway.run(LiteLLMRequest(
            prompt=_build_prompt(manifest, proposed_classification, confidence, reasons),
            metadata={
                "account_alias": str(manifest["account_alias"]),
                "attachment_id": str(manifest["attachment_id"]),
                "classification": proposed_classification,
            },
        ))
        warnings = list(response.warnings)
        warnings.append("human_review_required")
        return ClassificationProposal(
            manifest_path=str(path),
            attachment_id=str(manifest["attachment_id"]),
            account_alias=str(manifest["account_alias"]),
            dry_run=True,
            review_required=True,
            status="proposal_only",
            proposed_classification=proposed_classification,
            confidence=confidence,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
            llm_output_text=response.output_text,
            llm_provider=response.provider,
            llm_model=response.model,
            llm_total_tokens=response.total_tokens,
            llm_estimated_cost_eur=response.estimated_cost_eur,
        )

    def _heuristic_classification(self, manifest: Mapping[str, Any]) -> tuple[str, str, list[str]]:
        subject = str(manifest.get("subject") or "").strip()
        original_filename = str(manifest.get("original_filename") or "").strip()
        extension = str(manifest.get("file_extension") or "").strip().lower()
        combined = " ".join(part.casefold() for part in (subject, original_filename) if part)
        policy_result = self.policy.evaluate_filename(original_filename or f"file{extension}")
        reasons = [
            f"policy decision: {policy_result.decision.value}",
            f"extension: {extension or 'missing'}",
        ]
        if manifest.get("scan_result"):
            reasons.append(f"scan result: {manifest['scan_result']}")
        if manifest.get("status_reason"):
            reasons.append(f"status reason: {manifest['status_reason']}")
        if _contains_any(combined, ("fattura", "invoice", "ordine", "ordine-acquisto", "purchase")):
            reasons.append("matched invoice or purchase keywords")
            return "amministrazione_fattura", "medium", reasons
        if _contains_any(combined, ("verbale", "minutes", "meeting", "riunione")):
            reasons.append("matched meeting keywords")
            return "riunione_verbale", "medium", reasons
        if _contains_any(combined, ("report", "relazione", "summary", "riepilogo")):
            reasons.append("matched report keywords")
            return "report_documentale", "medium", reasons
        if policy_result.decision is PolicyDecision.ALLOW:
            reasons.append("no strong keyword match; keeping generic review queue")
            return "documento_generico_da_rivedere", "low", reasons
        if policy_result.decision is PolicyDecision.REVIEW:
            reasons.append("file type already requires review before classification")
            return "tipo_file_da_rivedere", "low", reasons
        reasons.append("file type denied; proposal kept outside automatic flows")
        return "contenuto_da_bloccare", "low", reasons


def classification_human_summary(result: ClassificationProposal) -> list[str]:
    lines = [
        f"Proposta classificazione: {result.proposed_classification} ({result.confidence})",
        f"Attachment: {result.attachment_id}; account: {result.account_alias}",
        "Revisione umana obbligatoria: si",
    ]
    if result.reasons:
        lines.append(f"Motivo principale: {result.reasons[0]}")
    if result.warnings:
        lines.append(f"Warning: {result.warnings[0]}")
    return lines


def review_classification_proposal(proposal_path: str | Path, *, decision: str, reviewer: str,
                                   review_notes: str = "") -> ClassificationReview:
    path = Path(proposal_path)
    proposal = _load_proposal(path)
    normalized_decision = decision.strip().lower()
    normalized_reviewer = reviewer.strip()
    notes = review_notes.strip()
    if normalized_decision not in {"approve", "reject"}:
        raise ClassificationProposalError("decision must be approve or reject")
    if not normalized_reviewer:
        raise ClassificationProposalError("reviewer is required")
    status = "approved_for_future_flow" if normalized_decision == "approve" else "rejected_for_manual_triage"
    warnings = list(proposal.warnings)
    warnings = [item for item in warnings if item != "human_review_required"]
    warnings.append(f"human_review_{normalized_decision}d")
    reasons = list(proposal.reasons)
    reasons.append(f"human review decision: {normalized_decision}")
    if notes:
        reasons.append(f"review notes: {notes}")
    return ClassificationReview(
        manifest_path=proposal.manifest_path,
        attachment_id=proposal.attachment_id,
        account_alias=proposal.account_alias,
        dry_run=True,
        status=status,
        proposed_classification=proposal.proposed_classification,
        reviewer=normalized_reviewer,
        decision=normalized_decision,
        review_completed=True,
        approved_for_future_flow=normalized_decision == "approve",
        review_notes=notes,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
    )


def classification_review_human_summary(result: ClassificationReview) -> list[str]:
    lines = [
        f"Review classificazione: {result.decision}",
        f"Classe proposta: {result.proposed_classification}",
        f"Attachment: {result.attachment_id}; reviewer: {result.reviewer}",
        f"Esito workflow futuro: {'abilitato' if result.approved_for_future_flow else 'bloccato'}",
    ]
    if result.review_notes:
        lines.append(f"Note review: {result.review_notes}")
    if result.warnings:
        lines.append(f"Warning: {result.warnings[-1]}")
    return lines


def _load_manifest(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise ClassificationProposalError(f"manifest not found: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClassificationProposalError(f"manifest is not valid JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise ClassificationProposalError("manifest must be a JSON object")
    for field in ("attachment_id", "account_alias", "original_filename", "subject"):
        value = manifest.get(field)
        if value is None or not str(value).strip():
            raise ClassificationProposalError(f"manifest field {field} is required")
    return manifest


def _load_proposal(path: Path) -> ClassificationProposal:
    if not path.is_file():
        raise ClassificationProposalError(f"proposal not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClassificationProposalError(f"proposal is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ClassificationProposalError("proposal must be a JSON object")
    if payload.get("dry_run") is not True:
        raise ClassificationProposalError("proposal must keep dry_run=true")
    if payload.get("review_required") is not True:
        raise ClassificationProposalError("proposal must require human review")
    if payload.get("status") != "proposal_only":
        raise ClassificationProposalError("proposal status must be proposal_only")
    try:
        return ClassificationProposal(
            manifest_path=str(payload["manifest_path"]),
            attachment_id=str(payload["attachment_id"]),
            account_alias=str(payload["account_alias"]),
            dry_run=bool(payload["dry_run"]),
            review_required=bool(payload["review_required"]),
            status=str(payload["status"]),
            proposed_classification=str(payload["proposed_classification"]),
            confidence=str(payload["confidence"]),
            reasons=tuple(str(item) for item in payload.get("reasons", [])),
            warnings=tuple(str(item) for item in payload.get("warnings", [])),
            llm_output_text=str(payload.get("llm_output_text", "")),
            llm_provider=str(payload.get("llm_provider", "")),
            llm_model=str(payload.get("llm_model", "")),
            llm_total_tokens=int(payload.get("llm_total_tokens", 0)),
            llm_estimated_cost_eur=float(payload.get("llm_estimated_cost_eur", 0.0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ClassificationProposalError("proposal payload is incomplete or malformed") from exc


def _build_prompt(manifest: Mapping[str, Any], classification: str, confidence: str,
                  reasons: list[str]) -> str:
    prompt = {
        "task": "Proponi una classificazione prudente per revisione umana, senza eseguire azioni automatiche.",
        "candidate_classification": classification,
        "confidence": confidence,
        "manifest": {
            "account_alias": manifest["account_alias"],
            "attachment_id": manifest["attachment_id"],
            "subject": manifest["subject"],
            "original_filename": manifest["original_filename"],
            "file_extension": manifest.get("file_extension"),
            "mime_type": manifest.get("mime_type"),
            "source_sender": manifest.get("source_sender"),
            "source_mailbox": manifest.get("source_mailbox"),
            "scan_result": manifest.get("scan_result"),
            "status_reason": manifest.get("status_reason"),
        },
        "reasons": reasons,
        "constraints": [
            "Nessuna azione automatica",
            "Conferma umana obbligatoria",
            "Usa solo metadati locali del manifest",
        ],
    }
    return json.dumps(prompt, ensure_ascii=False, separators=(",", ":"))


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)
