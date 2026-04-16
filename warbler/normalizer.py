"""Audio filename normalizer: sanitize and rename audio files consistently."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_SUPPORTED = {".mp3", ".flac", ".ogg", ".wav", ".m4a"}


@dataclass
class NormalizeResult:
    original: Path
    normalized: Path
    renamed: bool
    error: str | None = None


def _normalize_stem(stem: str) -> str:
    """Lowercase, replace whitespace/special chars with underscores."""
    stem = stem.lower().strip()
    stem = re.sub(r"[\s]+", "_", stem)
    stem = re.sub(r"[^a-z0-9_\-]", "", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem or "unnamed"


def normalize_filename(path: Path) -> NormalizeResult:
    """Return a NormalizeResult describing the normalized path."""
    if path.suffix.lower() not in _SUPPORTED:
        return NormalizeResult(
            original=path,
            normalized=path,
            renamed=False,
            error=f"Unsupported extension: {path.suffix}",
        )
    new_stem = _normalize_stem(path.stem)
    new_name = new_stem + path.suffix.lower()
    normalized = path.with_name(new_name)
    return NormalizeResult(
        original=path,
        normalized=normalized,
        renamed=(normalized.name != path.name),
    )


def apply_normalization(result: NormalizeResult, dry_run: bool = False) -> NormalizeResult:
    """Rename the file on disk unless dry_run is True."""
    if result.error or not result.renamed:
        return result
    if not dry_run:
        try:
            result.original.rename(result.normalized)
        except OSError as exc:
            return NormalizeResult(
                original=result.original,
                normalized=result.normalized,
                renamed=False,
                error=str(exc),
            )
    return result
