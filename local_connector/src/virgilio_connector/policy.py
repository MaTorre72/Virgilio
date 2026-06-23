"""Conservative filename-extension policy for the planning skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


DEFAULT_ALLOWED_EXTENSIONS = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"})
DEFAULT_DENIED_EXTENSIONS = frozenset(
    {
        ".exe", ".com", ".dll", ".msi", ".scr",
        ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jse", ".wsf", ".sh",
        ".lnk", ".url", ".hta", ".chm",
        ".iso", ".img", ".dmg", ".pkg",
        ".docm", ".xlsm", ".pptm",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".p7s", ".smime",
    }
)


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class PolicyResult:
    decision: PolicyDecision
    extension: str
    reason: str


@dataclass(frozen=True, slots=True)
class AttachmentPolicy:
    allowed_extensions: frozenset[str] = DEFAULT_ALLOWED_EXTENSIONS
    denied_extensions: frozenset[str] = DEFAULT_DENIED_EXTENSIONS

    def evaluate_filename(self, filename: str) -> PolicyResult:
        extension = Path(filename).suffix.lower()
        if extension in self.denied_extensions:
            return PolicyResult(PolicyDecision.DENY, extension, "extension is denied")
        if extension in self.allowed_extensions:
            return PolicyResult(
                PolicyDecision.ALLOW,
                extension,
                "extension is provisionally allowed; content checks are still required",
            )
        return PolicyResult(
            PolicyDecision.REVIEW,
            extension,
            "extension is neither allowed nor denied",
        )
