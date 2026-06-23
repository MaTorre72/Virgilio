"""Local file helpers with no mailbox or network side effects."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unicodedata


_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def sanitize_filename(filename: str, *, max_length: int = 150) -> str:
    """Return a portable basename, never a path.

    The function does not claim that the file content matches its extension.
    """

    if max_length < 16:
        raise ValueError("max_length must be at least 16")
    normalized = unicodedata.normalize("NFKC", str(filename or ""))
    basename = normalized.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = _INVALID_FILENAME_CHARS.sub("_", basename)
    cleaned = _WHITESPACE.sub("_", cleaned).strip(" ._")
    while ".." in cleaned:
        cleaned = cleaned.replace("..", ".")
    if not cleaned:
        cleaned = "attachment"

    path = Path(cleaned)
    suffix = path.suffix[:20]
    stem = path.stem if suffix else cleaned
    available = max_length - len(suffix)
    stem = stem[:available].rstrip(" ._") or "attachment"
    cleaned = f"{stem}{suffix}".rstrip(" .")

    if Path(cleaned).stem.upper() in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned[:max_length]


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Calculate SHA-256 for an existing regular file."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"not a regular file: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
