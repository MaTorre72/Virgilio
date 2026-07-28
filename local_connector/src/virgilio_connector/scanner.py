"""Optional local malware scanner boundary and Windows Defender adapter."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import os
import subprocess
from typing import Protocol


class ScanVerdict(StrEnum):
    CLEAN = "clean"
    INFECTED = "infected"
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class LocalScanResult:
    engine: str
    verdict: ScanVerdict
    detail: str


class LocalScanner(Protocol):
    """Shared boundary for Defender and a future ClamAV adapter."""

    @property
    def available(self) -> bool: ...

    def scan(self, path: Path) -> LocalScanResult: ...


@dataclass(frozen=True, slots=True)
class UnconfiguredScanner:
    reason: str = "no local scanner configured"

    @property
    def available(self) -> bool:
        return False

    def scan(self, path: Path) -> LocalScanResult:
        return LocalScanResult("none", ScanVerdict.UNVERIFIED, self.reason)


@dataclass(frozen=True, slots=True)
class WindowsDefenderScanner:
    executable: Path
    timeout_seconds: float = 120.0

    @classmethod
    def discover(cls, *, timeout_seconds: float = 120.0) -> "WindowsDefenderScanner | None":
        candidates: list[Path] = []
        program_data = os.environ.get("ProgramData")
        if program_data:
            platform = Path(program_data) / "Microsoft" / "Windows Defender" / "Platform"
            if platform.is_dir():
                candidates.extend(sorted(platform.glob("*/MpCmdRun.exe"), reverse=True))
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(Path(program_files) / "Windows Defender" / "MpCmdRun.exe")
        executable = next((path for path in candidates if path.is_file()), None)
        return cls(executable, timeout_seconds) if executable else None

    @property
    def available(self) -> bool:
        return self.executable.is_file()

    def scan(self, path: Path) -> LocalScanResult:
        source = Path(path)
        if not self.available:
            return LocalScanResult("windows_defender", ScanVerdict.UNVERIFIED,
                                   "Microsoft Defender executable is unavailable")
        if not source.is_file():
            return LocalScanResult("windows_defender", ScanVerdict.UNVERIFIED,
                                   "quarantine file is unavailable")
        source = source.resolve(strict=True)
        try:
            completed = subprocess.run(
                [str(self.executable), "-Scan", "-ScanType", "3", "-File", str(source),
                 "-DisableRemediation"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", timeout=self.timeout_seconds,
                check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.TimeoutExpired):
            return LocalScanResult("windows_defender", ScanVerdict.UNVERIFIED,
                                   "Microsoft Defender did not complete the scan")
        if completed.returncode == 0:
            return LocalScanResult("windows_defender", ScanVerdict.CLEAN,
                                   "scan completed with no threat reported")
        # Defender exit codes can vary by platform/version. A non-zero result is
        # deliberately not interpreted as clean or infected without stronger evidence.
        return LocalScanResult("windows_defender", ScanVerdict.UNVERIFIED,
                               f"scan returned non-zero status {completed.returncode}")


def select_scanner(mode: str = "auto") -> LocalScanner:
    normalized = mode.strip().lower()
    if normalized in {"", "auto", "windows_defender"}:
        defender = WindowsDefenderScanner.discover()
        if defender:
            return defender
        return UnconfiguredScanner("Microsoft Defender was not found")
    if normalized == "none":
        return UnconfiguredScanner()
    if normalized == "clamav":
        return UnconfiguredScanner("ClamAV adapter is not configured yet")
    raise ValueError(f"unsupported scanner mode: {mode}")
